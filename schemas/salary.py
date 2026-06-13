from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

class SalaryRevisionBase(BaseModel):
    annual_base_salary: Decimal
    monthly_allowance: Decimal = Decimal("0.00")
    monthly_deduction: Decimal = Decimal("0.00")
    currency: str

class SalaryRevisionCreate(SalaryRevisionBase):
    effective_from: date

class SalaryRevisionResponse(SalaryRevisionBase):
    id: UUID
    employee_id: UUID
    revision_number: int
    effective_from: date
    effective_to: Optional[date] = None
    is_current: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
