import statistics
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from clients.database import get_db
from models import Employee, Department, SalaryRevision
from schemas.employee import VALID_COUNTRY_CURRENCY
from schemas.analytics import (
    SalaryStats,
    DepartmentBreakdown,
    CountryBreakdown,
    SalaryBandDistribution,
    ExtremeSalariesResponse,
    ExtremeEmployeeSalary,
    AuditEmployee,
    SalaryAuditResponse
)
from dependencies.api_key_validator import api_key_validator

router = APIRouter(prefix="/analytics", tags=["Analytics V1"])

# Standard static exchange rates to USD for normalized reporting
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "INR": 0.012,
    "CAD": 0.73,
    "AUD": 0.66,
    "SGD": 0.74,
    "BRL": 0.18,
    "MXN": 0.055,
    "PLN": 0.25,
    "SEK": 0.095,
    "JPY": 0.0064
}

@router.get("/stats", response_model=SalaryStats)
def get_stats(db: Session = Depends(get_db), api_key: UUID = Depends(api_key_validator)):
    """
    Get overall active headcount, total base salary payroll, average, median, and salary range.
    Normalized to USD equivalent.
    """
    try:
        # Get count of total employees (including inactive)
        total_employees = db.query(Employee).filter(Employee.tenant_id == api_key).count()

        # Fetch current salary revision for active employees
        records = (
            db.query(SalaryRevision.annual_base_salary, SalaryRevision.currency)
            .join(Employee, SalaryRevision.employee_id == Employee.id)
            .filter(
                Employee.tenant_id == api_key,
                Employee.status == 1,
                SalaryRevision.is_current == True
            )
            .all()
        )

        active_employees = len(records)
        if active_employees == 0:
            return SalaryStats(
                total_employees=total_employees,
                active_employees=0,
                total_base_salary=0.0,
                avg_base_salary=0.0,
                median_base_salary=0.0,
                min_base_salary=0.0,
                max_base_salary=0.0
            )

        active_salaries_usd = []
        for r in records:
            rate = EXCHANGE_RATES.get(r.currency, 1.0)
            active_salaries_usd.append(float(r.annual_base_salary) * rate)

        return SalaryStats(
            total_employees=total_employees,
            active_employees=active_employees,
            total_base_salary=round(sum(active_salaries_usd), 2),
            avg_base_salary=round(statistics.mean(active_salaries_usd), 2),
            median_base_salary=round(statistics.median(active_salaries_usd), 2),
            min_base_salary=round(min(active_salaries_usd), 2),
            max_base_salary=round(max(active_salaries_usd), 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/departments", response_model=List[DepartmentBreakdown])
def get_departments_breakdown(db: Session = Depends(get_db), api_key: UUID = Depends(api_key_validator)):
    """
    Get headcount and average/total payroll per department (USD-equivalent).
    """
    try:
        records = (
            db.query(
                Department.name.label("department_name"),
                SalaryRevision.annual_base_salary,
                SalaryRevision.currency
            )
            .join(Employee, Department.id == Employee.department_id)
            .join(SalaryRevision, Employee.id == SalaryRevision.employee_id)
            .filter(
                Employee.tenant_id == api_key,
                Employee.status == 1,
                SalaryRevision.is_current == True
            )
            .all()
        )

        dept_map = {}
        for r in records:
            dept = r.department_name or "Unassigned"
            rate = EXCHANGE_RATES.get(r.currency, 1.0)
            salary_usd = float(r.annual_base_salary) * rate
            if dept not in dept_map:
                dept_map[dept] = []
            dept_map[dept].append(salary_usd)

        breakdown = []
        for dept, sals in dept_map.items():
            breakdown.append(DepartmentBreakdown(
                department=dept,
                employee_count=len(sals),
                avg_salary=round(statistics.mean(sals), 2) if sals else 0.0,
                total_salary=round(sum(sals), 2) if sals else 0.0
            ))

        # Sort by headcount descending
        breakdown.sort(key=lambda x: x.employee_count, reverse=True)
        return breakdown
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/countries", response_model=List[CountryBreakdown])
def get_countries_breakdown(db: Session = Depends(get_db), api_key: UUID = Depends(api_key_validator)):
    """
    Get headcount and average/total payroll per country (USD-equivalent).
    """
    try:
        records = (
            db.query(
                Employee.country,
                SalaryRevision.annual_base_salary,
                SalaryRevision.currency
            )
            .join(SalaryRevision, Employee.id == SalaryRevision.employee_id)
            .filter(
                Employee.tenant_id == api_key,
                Employee.status == 1,
                SalaryRevision.is_current == True
            )
            .all()
        )

        country_map = {}
        for r in records:
            c = r.country
            rate = EXCHANGE_RATES.get(r.currency, 1.0)
            salary_usd = float(r.annual_base_salary) * rate
            if c not in country_map:
                country_map[c] = []
            country_map[c].append(salary_usd)

        breakdown = []
        for country, sals in country_map.items():
            currency = VALID_COUNTRY_CURRENCY.get(country, "USD")
            breakdown.append(CountryBreakdown(
                country=country,
                currency=currency,
                employee_count=len(sals),
                avg_salary=round(statistics.mean(sals), 2) if sals else 0.0,
                total_salary=round(sum(sals), 2) if sals else 0.0
            ))

        # Sort by headcount descending
        breakdown.sort(key=lambda x: x.employee_count, reverse=True)
        return breakdown
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/salary-distribution", response_model=List[SalaryBandDistribution])
def get_salary_distribution(db: Session = Depends(get_db), api_key: UUID = Depends(api_key_validator)):
    """
    Groups active employees into base salary bands (USD-equivalent) for distribution analysis.
    """
    try:
        records = (
            db.query(SalaryRevision.annual_base_salary, SalaryRevision.currency)
            .join(Employee, SalaryRevision.employee_id == Employee.id)
            .filter(
                Employee.tenant_id == api_key,
                Employee.status == 1,
                SalaryRevision.is_current == True
            )
            .all()
        )

        bands = {
            "Under $50K": 0,
            "$50K - $100K": 0,
            "$100K - $150K": 0,
            "$150K - $200K": 0,
            "$200K - $250K": 0,
            "$250K+": 0
        }

        for r in records:
            rate = EXCHANGE_RATES.get(r.currency, 1.0)
            sal_usd = float(r.annual_base_salary) * rate
            if sal_usd < 50000:
                bands["Under $50K"] += 1
            elif sal_usd < 100000:
                bands["$50K - $100K"] += 1
            elif sal_usd < 150000:
                bands["$100K - $150K"] += 1
            elif sal_usd < 200000:
                bands["$150K - $200K"] += 1
            elif sal_usd < 250000:
                bands["$200K - $250K"] += 1
            else:
                bands["$250K+"] += 1

        return [
            SalaryBandDistribution(band=k, employee_count=v)
            for k, v in bands.items()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/extreme-salaries", response_model=ExtremeSalariesResponse)
def get_extreme_salaries(db: Session = Depends(get_db), api_key: UUID = Depends(api_key_validator)):
    """
    Returns lists of the Top 5 Highest Paid and Top 5 Lowest Paid active employees.
    """
    try:
        records = (
            db.query(
                Employee.id,
                Employee.employee_code,
                Employee.first_name,
                Employee.last_name,
                Department.name.label("department_name"),
                Employee.country,
                SalaryRevision.annual_base_salary,
                SalaryRevision.currency
            )
            .outerjoin(Department, Employee.department_id == Department.id)
            .join(SalaryRevision, Employee.id == SalaryRevision.employee_id)
            .filter(
                Employee.tenant_id == api_key,
                Employee.status == 1,
                SalaryRevision.is_current == True
            )
            .all()
        )

        all_records = []
        for r in records:
            rate = EXCHANGE_RATES.get(r.currency, 1.0)
            sal_usd = float(r.annual_base_salary) * rate
            all_records.append(ExtremeEmployeeSalary(
                id=str(r.id),
                employee_code=r.employee_code,
                first_name=r.first_name,
                last_name=r.last_name,
                department_name=r.department_name or "Unassigned",
                country=r.country,
                salary=float(r.annual_base_salary),
                currency=r.currency,
                salary_usd=sal_usd
            ))

        # Sort by USD salary descending
        all_records.sort(key=lambda x: x.salary_usd, reverse=True)

        highest = all_records[:5]
        # Sort ascending for lowest paid, take top 5
        lowest_sorted = sorted(all_records, key=lambda x: x.salary_usd)
        lowest = lowest_sorted[:5]

        return ExtremeSalariesResponse(
            highest_paid=highest,
            lowest_paid=lowest
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")


@router.get("/salary-audit", response_model=SalaryAuditResponse)
def get_salary_audit(db: Session = Depends(get_db), api_key: UUID = Depends(api_key_validator)):
    """
    Returns active employees categorized under pay equity concerns (Compa-Ratio < 0.85)
    and overdue salary reviews (days since last revision > 365).
    """
    from datetime import date
    try:
        records = (
            db.query(
                Employee.id,
                Employee.employee_code,
                Employee.first_name,
                Employee.last_name,
                Department.name.label("department_name"),
                Employee.country,
                SalaryRevision.annual_base_salary,
                SalaryRevision.currency,
                SalaryRevision.effective_from
            )
            .outerjoin(Department, Employee.department_id == Department.id)
            .join(SalaryRevision, Employee.id == SalaryRevision.employee_id)
            .filter(
                Employee.tenant_id == api_key,
                Employee.status == 1,
                SalaryRevision.is_current == True
            )
            .all()
        )

        # 1. Group active salaries to compute departmental averages in USD equivalents
        dept_salaries = {}
        for r in records:
            dept = r.department_name or "Unassigned"
            rate = EXCHANGE_RATES.get(r.currency, 1.0)
            sal_usd = float(r.annual_base_salary) * rate
            if dept not in dept_salaries:
                dept_salaries[dept] = []
            dept_salaries[dept].append(sal_usd)

        dept_averages = {}
        for dept, sals in dept_salaries.items():
            dept_averages[dept] = sum(sals) / len(sals) if sals else 0.0

        # 2. Auditing employees
        today = date.today()
        underpaid = []
        overdue = []

        for r in records:
            rate = EXCHANGE_RATES.get(r.currency, 1.0)
            sal_usd = float(r.annual_base_salary) * rate
            dept = r.department_name or "Unassigned"
            dept_avg = dept_averages.get(dept, 0.0)

            # Compa Ratio
            compa_ratio = (sal_usd / dept_avg) if dept_avg > 0 else 1.0

            # Time since revision
            rev_date = r.effective_from
            days_since = (today - rev_date).days if rev_date else 0

            emp_audit = AuditEmployee(
                id=str(r.id),
                employee_code=r.employee_code,
                first_name=r.first_name,
                last_name=r.last_name,
                department_name=dept,
                salary=float(r.annual_base_salary),
                currency=r.currency,
                salary_usd=sal_usd,
                compa_ratio=round(compa_ratio, 2),
                department_avg=round(dept_avg, 2),
                last_revision_date=str(rev_date) if rev_date else "",
                days_since_revision=days_since
            )

            # Underpaid check: less than 85% of department average
            if compa_ratio < 0.85:
                underpaid.append(emp_audit)

            # Overdue review check: last revision effective date was > 365 days ago
            if days_since > 365:
                overdue.append(emp_audit)

        # Sort underpaid by compa_ratio ascending (lowest ratio first)
        underpaid.sort(key=lambda x: x.compa_ratio)
        # Sort overdue by days_since_revision descending (most overdue first)
        overdue.sort(key=lambda x: x.days_since_revision, reverse=True)

        return SalaryAuditResponse(
            underpaid_employees=underpaid,
            overdue_reviews=overdue
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")
