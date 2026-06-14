from pydantic import BaseModel
from typing import List

class SalaryStats(BaseModel):
    total_employees: int
    active_employees: int
    total_base_salary: float
    avg_base_salary: float
    median_base_salary: float
    min_base_salary: float
    max_base_salary: float

class DepartmentBreakdown(BaseModel):
    department: str
    employee_count: int
    avg_salary: float
    total_salary: float

class CountryBreakdown(BaseModel):
    country: str
    currency: str
    employee_count: int
    avg_salary: float
    total_salary: float

class SalaryBandDistribution(BaseModel):
    band: str
    employee_count: int

class ExtremeEmployeeSalary(BaseModel):
    id: str
    employee_code: str
    first_name: str
    last_name: str
    department_name: str
    country: str
    salary: float
    currency: str
    salary_usd: float

class ExtremeSalariesResponse(BaseModel):
    highest_paid: List[ExtremeEmployeeSalary]
    lowest_paid: List[ExtremeEmployeeSalary]

class AuditEmployee(BaseModel):
    id: str
    employee_code: str
    first_name: str
    last_name: str
    department_name: str
    salary: float
    currency: str
    salary_usd: float
    compa_ratio: float = 0.0
    department_avg: float = 0.0
    last_revision_date: str = ""
    days_since_revision: int = 0

class SalaryAuditResponse(BaseModel):
    underpaid_employees: List[AuditEmployee]
    overdue_reviews: List[AuditEmployee]
