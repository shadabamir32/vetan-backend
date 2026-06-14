from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

class SalaryRevisionBase(BaseModel):
    annual_base_salary: Decimal
    monthly_allowance: Decimal = Decimal("0.00")
    monthly_deduction: Decimal = Decimal("0.00")
    currency: str

    @field_validator("annual_base_salary")
    @classmethod
    def validate_salary(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Annual base salary must be greater than 0.")
        return v

    @field_validator("monthly_allowance")
    @classmethod
    def validate_allowance(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Monthly allowance cannot be negative.")
        return v

    @field_validator("monthly_deduction")
    @classmethod
    def validate_deduction(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Monthly deduction cannot be negative.")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Currency cannot be empty or whitespace only.")
        return v.strip()

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
