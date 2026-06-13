from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from schemas.salary import SalaryRevisionResponse
from clients.database import SessionLocal
from models import Employee, Department

# Supported country-currency mappings based on seed configuration
VALID_COUNTRY_CURRENCY = {
    "United States": "USD",
    "United Kingdom": "GBP",
    "Germany": "EUR",
    "India": "INR",
    "Canada": "CAD",
    "Australia": "AUD",
    "France": "EUR",
    "Netherlands": "EUR",
    "Singapore": "SGD",
    "Brazil": "BRL",
    "Mexico": "MXN",
    "Poland": "PLN",
    "Spain": "EUR",
    "Sweden": "SEK",
    "Japan": "JPY"
}

class EmployeeBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    country: str
    department_id: Optional[UUID] = None
    status: int = 1
    joining_date: date

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_non_empty_names(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only.")
        return v.strip()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: int) -> int:
        if v not in (0, 1):
            raise ValueError("Status must be 0 (Inactive) or 1 (Active).")
        return v

class EmployeeCreate(EmployeeBase):
    # Initial salary fields to seed the initial salary revision
    annual_base_salary: Decimal
    monthly_allowance: Decimal = Decimal("0.00")
    monthly_deduction: Decimal = Decimal("0.00")
    currency: str

    @field_validator("email")
    @classmethod
    def validate_email_unique(cls, v: EmailStr) -> EmailStr:
        db = SessionLocal()
        try:
            existing = db.query(Employee).filter(Employee.email == v).first()
            if existing:
                raise ValueError("Email is already registered.")
        finally:
            db.close()
        return v

    @field_validator("department_id")
    @classmethod
    def validate_department_exists(cls, v: Optional[UUID]) -> Optional[UUID]:
        if v is not None:
            db = SessionLocal()
            try:
                dept = db.query(Department).filter_by(id=v).first()
                if not dept:
                    raise ValueError("Department does not exist.")
            finally:
                db.close()
        return v

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

    @model_validator(mode="after")
    def validate_country_and_currency(self) -> "EmployeeCreate":
        country = self.country
        currency = self.currency
        
        # 1. Validate country is supported
        if country not in VALID_COUNTRY_CURRENCY:
            raise ValueError(
                f"Country '{country}' is not supported. Supported countries: {list(VALID_COUNTRY_CURRENCY.keys())}"
            )
            
        # 2. Validate currency matches country
        expected_currency = VALID_COUNTRY_CURRENCY[country]
        if currency != expected_currency:
            raise ValueError(
                f"Currency '{currency}' does not match country '{country}'. Expected '{expected_currency}'."
            )
            
        return self

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    country: Optional[str] = None
    department_id: Optional[UUID] = None
    status: Optional[int] = None
    joining_date: Optional[date] = None
    termination_date: Optional[date] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_non_empty_names(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Name cannot be empty or whitespace only.")
            return v.strip()
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v not in (0, 1):
                raise ValueError("Status must be 0 (Inactive) or 1 (Active).")
        return v

    @field_validator("department_id")
    @classmethod
    def validate_department_exists(cls, v: Optional[UUID]) -> Optional[UUID]:
        if v is not None:
            db = SessionLocal()
            try:
                dept = db.query(Department).filter_by(id=v).first()
                if not dept:
                    raise ValueError("Department does not exist.")
            finally:
                db.close()
        return v

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if v not in VALID_COUNTRY_CURRENCY:
                raise ValueError(
                    f"Country '{v}' is not supported. Supported countries: {list(VALID_COUNTRY_CURRENCY.keys())}"
                )
        return v

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
