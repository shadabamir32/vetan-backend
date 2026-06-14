from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

class PayrollRunCreate(BaseModel):
    payroll_month: int
    payroll_year: int

    @field_validator("payroll_month")
    @classmethod
    def validate_month(cls, v: int) -> int:
        if not (1 <= v <= 12):
            raise ValueError("Payroll month must be between 1 and 12.")
        return v

    @field_validator("payroll_year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 2000:
            raise ValueError("Payroll year must be 2000 or later.")
        return v

class PayrollRecordResponse(BaseModel):
    id: UUID
    payroll_run_id: UUID
    employee_id: UUID
    employee_code: str
    first_name: str
    last_name: str
    department_name: Optional[str] = None
    country: str
    gross_amount: Decimal
    deduction_amount: Decimal
    net_amount: Decimal
    currency: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PayrollRunResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    payroll_month: int
    payroll_year: int
    status: int
    run_at: datetime
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PayrollRunDetailsResponse(PayrollRunResponse):
    total_gross: Decimal
    total_deduction: Decimal
    total_net: Decimal
    employee_count: int
    records: List[PayrollRecordResponse]

    model_config = ConfigDict(from_attributes=True)
