from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID, uuid4

from clients.database import get_db
from models import Employee, SalaryRevision
from schemas.employee import VALID_COUNTRY_CURRENCY
from schemas.salary import SalaryRevisionResponse, SalaryRevisionCreate
from dependencies.api_key_validator import api_key_validator

router = APIRouter(prefix="/employees", tags=["Salaries V1"])


@router.get("/{id}/salary-revisions", response_model=list[SalaryRevisionResponse])
def get_salary_history(
    id: str,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Retrieve all historical salary revisions for an employee, sorted by revision number ascending.
    """
    try:
        employee_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid employee ID format (must be a valid UUID).")

    employee = db.query(Employee).filter(Employee.id == employee_uuid, Employee.tenant_id == api_key).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    revisions = (
        db.query(SalaryRevision)
        .filter(SalaryRevision.employee_id == employee_uuid)
        .order_by(SalaryRevision.revision_number.asc())
        .all()
    )
    return revisions


@router.get("/{id}/current-salary", response_model=SalaryRevisionResponse)
def get_current_salary(
    id: str,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Retrieve the current active salary revision for an employee.
    """
    try:
        employee_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid employee ID format (must be a valid UUID).")

    employee = db.query(Employee).filter(Employee.id == employee_uuid, Employee.tenant_id == api_key).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    current_salary = (
        db.query(SalaryRevision)
        .filter(SalaryRevision.employee_id == employee_uuid, SalaryRevision.is_current == True)
        .first()
    )
    if not current_salary:
        raise HTTPException(status_code=404, detail="Current salary revision not found.")
        
    return current_salary


@router.post("/{id}/salary-revisions", response_model=SalaryRevisionResponse, status_code=201)
def create_salary_revision(
    id: str,
    payload: SalaryRevisionCreate,
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    Create a new compensation record (SCD Type 2 behavior) for an employee.
    """
    try:
        employee_uuid = UUID(id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid employee ID format (must be a valid UUID).")

    employee = db.query(Employee).filter(Employee.id == employee_uuid, Employee.tenant_id == api_key).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found.")

    # 1. Validate currency matches employee's country
    expected_currency = VALID_COUNTRY_CURRENCY.get(employee.country)
    if not expected_currency:
        raise HTTPException(status_code=422, detail=f"Employee country '{employee.country}' is not supported.")
    
    if payload.currency != expected_currency:
        raise HTTPException(
            status_code=422,
            detail=f"Currency '{payload.currency}' does not match country '{employee.country}'. Expected '{expected_currency}'."
        )

    # 2. Get current active salary revision
    current_salary = (
        db.query(SalaryRevision)
        .filter(SalaryRevision.employee_id == employee_uuid, SalaryRevision.is_current == True)
        .first()
    )

    if not current_salary:
        raise HTTPException(status_code=404, detail="Current salary revision not found.")

    # 3. Validate effective_from is strictly after current_salary.effective_from
    if payload.effective_from <= current_salary.effective_from:
        raise HTTPException(
            status_code=422,
            detail=f"New effective date ({payload.effective_from}) must be after the current active revision effective date ({current_salary.effective_from})."
        )

    # 4. Perform SCD Type 2 updates
    # Update old current revision
    current_salary.is_current = False
    current_salary.effective_to = payload.effective_from

    # Create new revision
    new_revision = SalaryRevision(
        id=uuid4(),
        employee_id=employee_uuid,
        annual_base_salary=payload.annual_base_salary,
        monthly_allowance=payload.monthly_allowance,
        monthly_deduction=payload.monthly_deduction,
        currency=payload.currency,
        revision_number=current_salary.revision_number + 1,
        effective_from=payload.effective_from,
        effective_to=None,
        is_current=True
    )
    db.add(new_revision)

    try:
        db.commit()
        db.refresh(new_revision)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during salary revision creation: {str(e)}")

    return new_revision
