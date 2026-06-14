from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from uuid import UUID, uuid4
from typing import Optional

from clients.database import get_db
from models import Department, Employee, SalaryRevision, Tenant
from schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from schemas.salary import SalaryRevisionResponse
from dependencies.api_key_validator import api_key_validator

router = APIRouter(prefix="/employees", tags=["Employees V1"])


@router.get("", response_model=dict)
def get_employees(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
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

