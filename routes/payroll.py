import calendar
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session, joinedload
from uuid import UUID, uuid4

from clients.database import get_db
from models import Employee, SalaryRevision, PayrollRun, PayrollRecord
from schemas.payroll import (
    PayrollRunCreate,
    PayrollRunResponse,
    PayrollRecordResponse,
    PayrollRunDetailsResponse
)
from dependencies.api_key_validator import api_key_validator

router = APIRouter(prefix="/payroll", tags=["Payroll V1"])


@router.post("/run", response_model=PayrollRunResponse, status_code=201)
def run_payroll(
    payload: PayrollRunCreate,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Run payroll calculations for the active tenant's eligible employees for a selected month/year.
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
        raise HTTPException(
            status_code=400,
            detail="Payroll run already exists for the specified month and year."
        )

    # Calculate start and end date of the month
    start_of_month = date(payload.payroll_year, payload.payroll_month, 1)
    _, num_days = calendar.monthrange(payload.payroll_year, payload.payroll_month)
    last_day_of_month = date(payload.payroll_year, payload.payroll_month, num_days)

    # 2. Query eligible employees:
    # - Joined on or before the last day of the payroll month
    # - Active (status == 1) OR (deactivated (status == 0) AND (termination_date is None or termination_date >= start_of_month))
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
        .all()
    )

    if not eligible_employees:
        raise HTTPException(
            status_code=400,
            detail="No eligible employees found for the specified payroll period."
        )

    # Create the PayrollRun in status 2 (Processed)
    payroll_run = PayrollRun(
        id=uuid4(),
        tenant_id=api_key,
        payroll_month=payload.payroll_month,
        payroll_year=payload.payroll_year,
        status=2,
        run_at=datetime.utcnow()
    )
    db.add(payroll_run)

    try:
        # Flush so that payroll_run.id is populated for records
        db.flush()

        for employee in eligible_employees:
            # 3. Resolve active salary revision on the last day of the month:
            # - effective_from <= last_day_of_month
            # - effective_to is None OR effective_to > last_day_of_month
            salary_revision = (
                db.query(SalaryRevision)
                .filter(
                    SalaryRevision.employee_id == employee.id,
                    SalaryRevision.effective_from <= last_day_of_month,
                    or_(
                        SalaryRevision.effective_to == None,
                        SalaryRevision.effective_to > last_day_of_month
                    )
                )
                .order_by(SalaryRevision.revision_number.desc())
                .first()
            )

            if not salary_revision:
                raise HTTPException(
                    status_code=400,
                    detail=f"Employee {employee.employee_code} does not have an active salary revision for the specified payroll period."
                )

            # 4. Perform calculations
            # Net Payroll = (Annual Base Salary / 12) + Allowance - Deduction
            gross_amount = (salary_revision.annual_base_salary / Decimal("12.00")) + salary_revision.monthly_allowance
            deduction_amount = salary_revision.monthly_deduction
            net_amount = gross_amount - deduction_amount

            # Round to two decimal places
            gross_amount = gross_amount.quantize(Decimal("0.01"))
            deduction_amount = deduction_amount.quantize(Decimal("0.01"))
            net_amount = net_amount.quantize(Decimal("0.01"))

            # Create the PayrollRecord
            payroll_record = PayrollRecord(
                id=uuid4(),
                payroll_run_id=payroll_run.id,
                employee_id=employee.id,
                gross_amount=gross_amount,
                deduction_amount=deduction_amount,
                net_amount=net_amount,
                currency=salary_revision.currency,
                created_at=datetime.utcnow()
            )
            db.add(payroll_record)

        db.commit()
        db.refresh(payroll_run)
        return payroll_run

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error during payroll processing: {str(e)}"
        )


@router.get("/runs", response_model=list[PayrollRunResponse])
def get_payroll_runs(
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Retrieve history of all payroll runs for the active tenant.
    """
    try:
        runs = (
            db.query(PayrollRun)
            .filter(PayrollRun.tenant_id == api_key)
            .order_by(PayrollRun.run_at.desc())
            .all()
        )
        return runs
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@router.get("/runs/{id}", response_model=PayrollRunDetailsResponse)
def get_payroll_run_details(
    id: str,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Retrieve details of a specific payroll run including compiled totals and employee records.
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
        records = (
            db.query(PayrollRecord)
            .filter(PayrollRecord.payroll_run_id == run_uuid)
            .options(
                joinedload(PayrollRecord.employee).joinedload(Employee.department)
            )
            .all()
        )

        record_responses = []
        total_gross = Decimal("0.00")
        total_deduction = Decimal("0.00")
        total_net = Decimal("0.00")

        for rec in records:
            emp = rec.employee
            dept_name = emp.department.name if emp.department else None

            total_gross += rec.gross_amount
            total_deduction += rec.deduction_amount
            total_net += rec.net_amount

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
            total_gross=total_gross,
            total_deduction=total_deduction,
            total_net=total_net,
            employee_count=len(records),
            records=record_responses
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
