import calendar
import time
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session, joinedload
from uuid import UUID, uuid4
from typing import Optional

from clients.database import get_db, SessionLocal
from models import Employee, SalaryRevision, PayrollRun, PayrollRecord
from schemas.payroll import (
    PayrollRunCreate,
    PayrollRunResponse,
    PayrollRecordResponse,
    PayrollRunDetailsResponse,
    PaginatedPayrollRunsResponse
)
from dependencies.api_key_validator import api_key_validator

router = APIRouter(prefix="/payroll", tags=["Payroll V1"])


def process_payroll_in_background(payroll_run_id: UUID, api_key: UUID, max_retries: int = 3) -> None:
    """
    Background worker that runs the payroll calculations for a given run ID.
    Transitions status to In Progress (1), runs calculations in chunks of 1000 with transaction isolation,
    and handles retries. Transitions status to Processed (2) on success, or Failure (4)
    after all retries fail.
    """
    db = SessionLocal()
    for attempt in range(max_retries):
        try:
            # 1. Update status to In Progress (1)
            run = db.query(PayrollRun).filter(PayrollRun.id == payroll_run_id).first()
            if not run:
                db.close()
                return
            run.status = 1
            db.commit()

            # Begin processing calculations under a single transaction
            # Delete any existing records for this run (ensuring idempotency/atomicity on retry)
            db.query(PayrollRecord).filter(PayrollRecord.payroll_run_id == payroll_run_id).delete()

            # Calculate dates
            start_of_month = date(run.payroll_year, run.payroll_month, 1)
            _, num_days = calendar.monthrange(run.payroll_year, run.payroll_month)
            last_day_of_month = date(run.payroll_year, run.payroll_month, num_days)

            # Process in chunks of 1000
            chunk_size = 1000
            offset = 0
            processed_count = 0
            skipped_employees = []
            has_employees = False

            while True:
                # Retrieve a chunk of eligible employees with eager loaded salary revisions
                eligible_employees = (
                    db.query(Employee)
                    .filter(
                        Employee.tenant_id == api_key,
                        Employee.joining_date <= last_day_of_month,
                        or_(
                            Employee.status == 1,
                            Employee.termination_date == None,
                            Employee.termination_date >= start_of_month
                        )
                    )
                    .order_by(Employee.id)
                    .options(joinedload(Employee.salary_revisions))
                    .limit(chunk_size)
                    .offset(offset)
                    .all()
                )

                if not eligible_employees:
                    break

                has_employees = True
                records_to_insert = []

                # Process this chunk
                for employee in eligible_employees:
                    # Resolve active salary revision on the last day of the month in-memory
                    active_revision = None
                    for revision in employee.salary_revisions:
                        if revision.effective_from <= last_day_of_month:
                            if revision.effective_to is None or revision.effective_to > last_day_of_month:
                                if (active_revision is None or 
                                        revision.revision_number > active_revision.revision_number):
                                    active_revision = revision

                    if not active_revision:
                        skipped_employees.append(employee.employee_code)
                        continue

                    # Net Payroll = (Annual Base Salary / 12) + Allowance - Deduction
                    gross_amount = (active_revision.annual_base_salary / Decimal("12.00")) + active_revision.monthly_allowance
                    deduction_amount = active_revision.monthly_deduction
                    net_amount = gross_amount - deduction_amount

                    # Round to two decimal places
                    gross_amount = gross_amount.quantize(Decimal("0.01"))
                    deduction_amount = deduction_amount.quantize(Decimal("0.01"))
                    net_amount = net_amount.quantize(Decimal("0.01"))

                    payroll_record = PayrollRecord(
                        id=uuid4(),
                        payroll_run_id=payroll_run_id,
                        employee_id=employee.id,
                        gross_amount=gross_amount,
                        deduction_amount=deduction_amount,
                        net_amount=net_amount,
                        currency=active_revision.currency,
                        created_at=datetime.utcnow()
                    )
                    records_to_insert.append(payroll_record)
                    processed_count += 1

                if records_to_insert:
                    db.bulk_save_objects(records_to_insert)

                offset += chunk_size

            # If there were eligible employees, but all of them were skipped
            if has_employees and processed_count == 0:
                raise ValueError("No eligible employees had active salary revisions.")

            # Finalize run state to Processed (2)
            run = db.query(PayrollRun).filter(PayrollRun.id == payroll_run_id).first()
            run.status = 2
            
            if not has_employees:
                run.message = "Processed successfully with 0 records."
            elif not skipped_employees:
                run.message = f"Processed successfully with {processed_count} records."
            else:
                run.message = f"Processed successfully with {processed_count} records. Skipped {len(skipped_employees)} employees due to missing revisions (Codes: {', '.join(skipped_employees)})."
                
            db.commit()
            db.close()
            return

        except Exception as e:
            db.rollback()
            # If this was the last attempt, set status to Failure (4) and save error message
            if attempt == max_retries - 1:
                try:
                    run = db.query(PayrollRun).filter(PayrollRun.id == payroll_run_id).first()
                    if run:
                        run.status = 4
                        run.message = f"Failed: {str(e)}"
                        db.commit()
                except Exception:
                    db.rollback()
            else:
                # Brief delay before retrying
                time.sleep(0.1)

    db.close()


@router.post("/run", response_model=PayrollRunResponse, status_code=201)
def run_payroll(
    payload: PayrollRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Queue payroll calculations for the active tenant's eligible employees for a selected month/year.
    """
    # 1. Uniqueness check: check if a run already exists for this tenant/month/year
    existing_run = (
        db.query(PayrollRun)
        .filter(
            PayrollRun.tenant_id == api_key,
            PayrollRun.payroll_month == payload.payroll_month,
            PayrollRun.payroll_year == payload.payroll_year
        )
        .first()
    )
    if existing_run:
        if existing_run.status == 1:
            raise HTTPException(
                status_code=400,
                detail="Payroll run is currently in progress."
            )
        elif existing_run.status == 0:
            raise HTTPException(
                status_code=400,
                detail="Payroll run is already queued and pending."
            )
        elif existing_run.status in (2, 4):
            # Re-queue processed or failed run: reset status to Pending (0)
            existing_run.status = 0
            existing_run.run_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_run)
            background_tasks.add_task(process_payroll_in_background, existing_run.id, api_key)
            return existing_run

    # Create the PayrollRun in status Pending (0)
    payroll_run = PayrollRun(
        id=uuid4(),
        tenant_id=api_key,
        payroll_month=payload.payroll_month,
        payroll_year=payload.payroll_year,
        status=0,
        run_at=datetime.utcnow()
    )
    db.add(payroll_run)

    try:
        db.commit()
        db.refresh(payroll_run)
        # Add background task
        background_tasks.add_task(process_payroll_in_background, payroll_run.id, api_key)
        return payroll_run

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error during payroll queueing: {str(e)}"
        )


@router.get("/runs", response_model=PaginatedPayrollRunsResponse)
def get_payroll_runs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    payroll_month: Optional[int] = Query(None, ge=1, le=12),
    payroll_year: Optional[int] = Query(None, ge=2000),
    status: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Retrieve history of all payroll runs for the active tenant (paginated and filterable).
    """
    try:
        query = db.query(PayrollRun).filter(PayrollRun.tenant_id == api_key)

        # Apply month filter
        if payroll_month is not None:
            query = query.filter(PayrollRun.payroll_month == payroll_month)

        # Apply year filter
        if payroll_year is not None:
            query = query.filter(PayrollRun.payroll_year == payroll_year)

        # Apply status filter
        if status is not None:
            query = query.filter(PayrollRun.status == status)

        total = query.count()
        pages = (total + limit - 1) // limit if total > 0 else 1
        offset = (page - 1) * limit

        runs = (
            query
            .order_by(PayrollRun.run_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return PaginatedPayrollRunsResponse(
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            data=runs
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get("/runs/{id}", response_model=PayrollRunDetailsResponse)
def get_payroll_run_details(
    id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Retrieve details of a specific payroll run including compiled totals and employee records (paginated and filterable).
    """
    try:
        run_uuid = UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid payroll run ID format (must be a valid UUID)."
        )

    run = (
        db.query(PayrollRun)
        .filter(PayrollRun.id == run_uuid, PayrollRun.tenant_id == api_key)
        .first()
    )
    if not run:
        raise HTTPException(
            status_code=404,
            detail="Payroll run not found."
        )

    try:
        # Compute aggregate totals directly in the database (efficient, database-agnostic, run-wide)
        totals = (
            db.query(
                func.sum(PayrollRecord.gross_amount).label("total_gross"),
                func.sum(PayrollRecord.deduction_amount).label("total_deduction"),
                func.sum(PayrollRecord.net_amount).label("total_net"),
                func.count(PayrollRecord.id).label("employee_count")
            )
            .filter(PayrollRecord.payroll_run_id == run_uuid)
            .first()
        )

        total_gross = totals.total_gross or Decimal("0.00")
        total_deduction = totals.total_deduction or Decimal("0.00")
        total_net = totals.total_net or Decimal("0.00")
        employee_count = totals.employee_count or 0

        # Build query for filtered records
        records_query = (
            db.query(PayrollRecord)
            .join(Employee, PayrollRecord.employee_id == Employee.id)
            .filter(PayrollRecord.payroll_run_id == run_uuid)
        )

        # Apply search keyword
        if search:
            search_filter = f"%{search}%"
            records_query = records_query.filter(
                (Employee.first_name.ilike(search_filter)) |
                (Employee.last_name.ilike(search_filter)) |
                (Employee.email.ilike(search_filter)) |
                (Employee.employee_code.ilike(search_filter))
            )

        # Apply department filter
        if department_id:
            try:
                dept_uuid = UUID(department_id)
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid department_id format (must be a valid UUID).")
            records_query = records_query.filter(Employee.department_id == dept_uuid)

        # Apply country filter
        if country:
            records_query = records_query.filter(Employee.country == country)

        # Calculate filtered count
        filtered_count = records_query.count()

        # Calculate pages based on the filtered count
        pages = (filtered_count + limit - 1) // limit if filtered_count > 0 else 1

        offset = (page - 1) * limit
        records = (
            records_query
            .options(
                joinedload(PayrollRecord.employee).joinedload(Employee.department)
            )
            .order_by(PayrollRecord.id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        record_responses = []
        for rec in records:
            emp = rec.employee
            dept_name = emp.department.name if emp.department else None

            rec_resp = PayrollRecordResponse(
                id=rec.id,
                payroll_run_id=rec.payroll_run_id,
                employee_id=rec.employee_id,
                employee_code=emp.employee_code,
                first_name=emp.first_name,
                last_name=emp.last_name,
                department_name=dept_name,
                country=emp.country,
                gross_amount=rec.gross_amount,
                deduction_amount=rec.deduction_amount,
                net_amount=rec.net_amount,
                currency=rec.currency,
                payroll_month=run.payroll_month,
                payroll_year=run.payroll_year,
                created_at=rec.created_at
            )
            record_responses.append(rec_resp)

        return PayrollRunDetailsResponse(
            id=run.id,
            tenant_id=run.tenant_id,
            payroll_month=run.payroll_month,
            payroll_year=run.payroll_year,
            status=run.status,
            run_at=run.run_at,
            message=run.message,
            total_gross=total_gross,
            total_deduction=total_deduction,
            total_net=total_net,
            employee_count=employee_count,
            filtered_count=filtered_count,
            page=page,
            limit=limit,
            pages=pages,
            records=record_responses
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
