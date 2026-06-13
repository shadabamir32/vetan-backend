from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import Optional

from clients.database import get_db
from models import Employee
from schemas.employee import EmployeeResponse
from schemas.salary import SalaryRevisionResponse
from dependencies.api_key_validator import api_key_validator

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=dict)
def get_employees(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    department_id: Optional[UUID] = Query(None),
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
        query = query.filter(Employee.department_id == department_id)
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

