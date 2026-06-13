from pydantic import BaseModel, ConfigDict, EmailStr
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from schemas.salary import SalaryRevisionResponse

class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    country: str
    department_id: Optional[UUID] = None
    status: int = 1
    joining_date: date

class EmployeeCreate(EmployeeBase):
    # Initial salary fields to seed the initial salary revision
    annual_base_salary: Decimal
    monthly_allowance: Decimal = Decimal("0.00")
    monthly_deduction: Decimal = Decimal("0.00")
    currency: str

class EmployeeResponse(EmployeeBase):
    id: UUID
    tenant_id: UUID
    employee_code: str
    termination_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    
    # Custom resolved properties
    department_name: Optional[str] = None
    current_salary: Optional[SalaryRevisionResponse] = None

    model_config = ConfigDict(from_attributes=True)
