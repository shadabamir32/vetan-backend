from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from uuid import UUID, uuid4
from typing import Optional, List
from datetime import date, datetime
import calendar
from decimal import Decimal
from sqlalchemy import or_

from clients.database import get_db
from models import Department, Employee, SalaryRevision, Tenant, PayrollRun, PayrollRecord
from schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from schemas.salary import SalaryRevisionResponse
from schemas.payroll import PayrollRecordResponse
from dependencies.api_key_validator import api_key_validator

router = APIRouter(prefix="/employees", tags=["Employees V1"])


@router.get("", response_model=dict)
def get_employees(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
    search: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    status: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Get paginated employees for the active tenant.
    Supports filtering by department, country, and status, and fuzzy search on profile fields.
    """
    query = db.query(Employee).filter(Employee.tenant_id == api_key)


    # Apply search keyword
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Employee.first_name.ilike(search_filter)) |
            (Employee.last_name.ilike(search_filter)) |
            (Employee.email.ilike(search_filter)) |
            (Employee.employee_code.ilike(search_filter))
        )

    # Apply filters
    if department_id:
        try:
            dept_uuid = UUID(department_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid department_id format (must be a valid UUID).")
        query = query.filter(Employee.department_id == dept_uuid)
    if country:
        query = query.filter(Employee.country == country)
    if status is not None:
        query = query.filter(Employee.status == status)

    total = query.count()
    offset = (page - 1) * limit

    # Eager load department and salary revisions to prevent N+1 query issues
    employees_list = (
        query.options(
            joinedload(Employee.department),
            joinedload(Employee.salary_revisions)
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    data = []
    for emp in employees_list:
        curr_sal = next((sr for sr in emp.salary_revisions if sr.is_current), None)
        emp_resp = EmployeeResponse.model_validate(emp)
        emp_resp.department_name = emp.department.name if emp.department else None
        emp_resp.current_salary = SalaryRevisionResponse.model_validate(curr_sal) if curr_sal else None
        data.append(emp_resp)

    pages = (total + limit - 1) // limit

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
        "data": data
    }


@router.post("", response_model=EmployeeResponse, status_code=201)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Onboard a new employee for the tenant.
    Creates both the employee profile and their initial salary revision record.
    """
    # Generate employee code based on current employee count
    count = db.query(Employee).filter(Employee.tenant_id == api_key).count()
    # Fetch tenant name for code generation. Tenant is already validated by dependency.
    tenant = db.query(Tenant).filter_by(id=api_key).first()
    employee_code = f"{tenant.name}-{((count + 1) * 10):05d}"  # Matches the naming format ACME-xxxxx

    emp_id = uuid4()
    employee = Employee(
        id=emp_id,
        tenant_id=api_key,
        department_id=payload.department_id,
        employee_code=employee_code,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        country=payload.country,
        status=payload.status,
        joining_date=payload.joining_date
    )
    db.add(employee)

    # Create initial salary revision
    salary = SalaryRevision(
        id=uuid4(),
        employee_id=emp_id,
        annual_base_salary=payload.annual_base_salary,
        monthly_allowance=payload.monthly_allowance,
        monthly_deduction=payload.monthly_deduction,
        currency=payload.currency,
        revision_number=1,
        effective_from=payload.joining_date,
        effective_to=None,
        is_current=True
    )
    db.add(salary)

    try:
        db.commit()
        db.refresh(employee)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during creation: {str(e)}")

    # Load department name
    dept_name = employee.department.name if employee.department else None

    # Construct response
    resp = EmployeeResponse.model_validate(employee)
    resp.department_name = dept_name
    resp.current_salary = SalaryRevisionResponse.model_validate(salary)

    return resp


@router.put("/{id}", response_model=EmployeeResponse)
def update_employee(
    id: str,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Update employee profile fields.
    """
    try:
        employee_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid employee ID format (must be a valid UUID).")

    employee = (
        db.query(Employee)
        .options(joinedload(Employee.department), joinedload(Employee.salary_revisions))
        .filter(Employee.id == employee_uuid, Employee.tenant_id == api_key)
        .first()
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    # Validate Department if updated
    if payload.department_id is not None:
        dept = db.query(Department).filter_by(id=payload.department_id, tenant_id=api_key).first()
        if not dept:
            raise HTTPException(status_code=422, detail="Department does not exist or belong to this tenant.")
        employee.department_id = payload.department_id
    if payload.email is not None:
        # Check duplicate email
        existing = db.query(Employee).filter(Employee.email == payload.email, Employee.id != employee_uuid).first()
        if existing:
            raise HTTPException(status_code=422, detail="Email is already in use by another employee.")
    
    # Update simple fields
    if payload.first_name is not None:
        employee.first_name = payload.first_name
    if payload.last_name is not None:
        employee.last_name = payload.last_name
    if payload.email is not None:
        employee.email = payload.email
    if payload.country is not None:
        employee.country = payload.country
    if payload.status is not None:
        employee.status = payload.status
    if payload.joining_date is not None:
        employee.joining_date = payload.joining_date
    if payload.termination_date is not None:
        employee.termination_date = payload.termination_date

    try:
        db.commit()
        db.refresh(employee)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during update: {str(e)}")

    curr_sal = next((sr for sr in employee.salary_revisions if sr.is_current), None)
    
    resp = EmployeeResponse.model_validate(employee)
    resp.department_name = employee.department.name if employee.department else None
    resp.current_salary = SalaryRevisionResponse.model_validate(curr_sal) if curr_sal else None

    return resp


@router.get("/{id}", response_model=EmployeeResponse)
def get_employee(
    id: str,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Get detailed profile of a specific employee for the active tenant.
    Includes department details and current salary information.
    """
    try:
        employee_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid employee ID format (must be a valid UUID).")

    employee = (
        db.query(Employee)
        .options(
            joinedload(Employee.department),
            joinedload(Employee.salary_revisions)
        )
        .filter(Employee.id == employee_uuid, Employee.tenant_id == api_key)
        .first()
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    curr_sal = next((sr for sr in employee.salary_revisions if sr.is_current), None)

    resp = EmployeeResponse.model_validate(employee)
    resp.department_name = employee.department.name if employee.department else None
    resp.current_salary = SalaryRevisionResponse.model_validate(curr_sal) if curr_sal else None

    return resp


@router.get("/{id}/payroll-history", response_model=List[PayrollRecordResponse])
def get_employee_payroll_history(
    id: str,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Get all processed payroll records for a specific employee of the active tenant.
    """
    try:
        employee_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid employee ID format (must be a valid UUID).")

    employee = db.query(Employee).filter(Employee.id == employee_uuid, Employee.tenant_id == api_key).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    records = (
        db.query(PayrollRecord)
        .join(PayrollRun, PayrollRecord.payroll_run_id == PayrollRun.id)
        .filter(
            PayrollRecord.employee_id == employee_uuid,
            PayrollRun.tenant_id == api_key,
            PayrollRun.status == 2  # Processed runs
        )
        .order_by(PayrollRun.payroll_year.desc(), PayrollRun.payroll_month.desc())
        .all()
    )

    res = []
    for rec in records:
        dept_name = employee.department.name if employee.department else None
        res.append(PayrollRecordResponse(
            id=rec.id,
            payroll_run_id=rec.payroll_run_id,
            employee_id=rec.employee_id,
            employee_code=employee.employee_code,
            first_name=employee.first_name,
            last_name=employee.last_name,
            department_name=dept_name,
            country=employee.country,
            gross_amount=rec.gross_amount,
            deduction_amount=rec.deduction_amount,
            net_amount=rec.net_amount,
            currency=rec.currency,
            payroll_month=rec.payroll_run.payroll_month,
            payroll_year=rec.payroll_run.payroll_year,
            created_at=rec.created_at
        ))
    return res


@router.post("/{id}/run-payroll", response_model=PayrollRecordResponse, status_code=201)
def run_individual_payroll(
    id: str,
    payload: dict,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Generate or upsert a payroll record for a single employee for a specific month and year.
    """
    try:
        employee_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid employee ID format (must be a valid UUID).")

    payroll_month = payload.get("payroll_month")
    payroll_year = payload.get("payroll_year")

    if payroll_month is None or not (1 <= payroll_month <= 12):
        raise HTTPException(status_code=422, detail="Valid payroll_month (1-12) is required.")
    if payroll_year is None or payroll_year < 2000:
        raise HTTPException(status_code=422, detail="Valid payroll_year (>= 2000) is required.")

    employee = (
        db.query(Employee)
        .options(joinedload(Employee.department), joinedload(Employee.salary_revisions))
        .filter(Employee.id == employee_uuid, Employee.tenant_id == api_key)
        .first()
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    # Check joining and termination eligibility
    _, num_days = calendar.monthrange(payroll_year, payroll_month)
    last_day_of_month = date(payroll_year, payroll_month, num_days)
    start_of_month = date(payroll_year, payroll_month, 1)

    if employee.joining_date > last_day_of_month:
        raise HTTPException(status_code=400, detail="Employee had not joined yet by the end of this month.")
    if employee.termination_date and employee.termination_date < start_of_month:
        raise HTTPException(status_code=400, detail="Employee was terminated prior to this month.")

    # Find active salary revision for the target month
    active_revision = None
    for revision in employee.salary_revisions:
        if revision.effective_from <= last_day_of_month:
            if revision.effective_to is None or revision.effective_to > last_day_of_month:
                if active_revision is None or revision.revision_number > active_revision.revision_number:
                    active_revision = revision

    if not active_revision:
        raise HTTPException(status_code=400, detail="No active salary revision found for the target month.")

    # Find or create payroll run
    run = (
        db.query(PayrollRun)
        .filter(
            PayrollRun.tenant_id == api_key,
            PayrollRun.payroll_month == payroll_month,
            PayrollRun.payroll_year == payroll_year
        )
        .first()
    )

    if not run:
        run = PayrollRun(
            id=uuid4(),
            tenant_id=api_key,
            payroll_month=payroll_month,
            payroll_year=payroll_year,
            status=2,  # Processed
            run_at=datetime.utcnow(),
            message=f"Individual payroll run initiated for employee {employee.employee_code}."
        )
        db.add(run)
        db.commit()
        db.refresh(run)
    elif run.status == 1:
        raise HTTPException(status_code=400, detail="Cannot update record. Main payroll run is currently in progress.")

    # Compute amount
    gross_amount = (active_revision.annual_base_salary / Decimal("12.00")) + active_revision.monthly_allowance
    deduction_amount = active_revision.monthly_deduction
    net_amount = gross_amount - deduction_amount

    # Round to two decimal places
    gross_amount = gross_amount.quantize(Decimal("0.01"))
    deduction_amount = deduction_amount.quantize(Decimal("0.01"))
    net_amount = net_amount.quantize(Decimal("0.01"))

    # Upsert record
    record = (
        db.query(PayrollRecord)
        .filter(
            PayrollRecord.payroll_run_id == run.id,
            PayrollRecord.employee_id == employee_uuid
        )
        .first()
    )

    if record:
        record.gross_amount = gross_amount
        record.deduction_amount = deduction_amount
        record.net_amount = net_amount
        record.currency = active_revision.currency
        record.created_at = datetime.utcnow()
    else:
        record = PayrollRecord(
            id=uuid4(),
            payroll_run_id=run.id,
            employee_id=employee_uuid,
            gross_amount=gross_amount,
            deduction_amount=deduction_amount,
            net_amount=net_amount,
            currency=active_revision.currency,
            created_at=datetime.utcnow()
        )
        db.add(record)

    try:
        db.commit()
        db.refresh(record)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    dept_name = employee.department.name if employee.department else None
    return PayrollRecordResponse(
        id=record.id,
        payroll_run_id=record.payroll_run_id,
        employee_id=record.employee_id,
        employee_code=employee.employee_code,
        first_name=employee.first_name,
        last_name=employee.last_name,
        department_name=dept_name,
        country=employee.country,
        gross_amount=record.gross_amount,
        deduction_amount=record.deduction_amount,
        net_amount=record.net_amount,
        currency=record.currency,
        payroll_month=run.payroll_month,
        payroll_year=run.payroll_year,
        created_at=record.created_at
    )


