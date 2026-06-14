import pytest
from datetime import date
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Tenant, Employee, SalaryRevision, Department

def create_test_employee(
    db: Session,
    tenant_id: UUID,
    department_id: UUID,
    first_name: str,
    last_name: str,
    email: str
) -> Employee:
    emp_id = uuid4()
    employee = Employee(
        id=emp_id,
        tenant_id=tenant_id,
        department_id=department_id,
        employee_code=f"TEST-{first_name.upper()}",
        first_name=first_name,
        last_name=last_name,
        email=email,
        country="United States",
        status=1,
        joining_date=date(2020, 1, 1)
    )
    db.add(employee)
    
    salary = SalaryRevision(
        id=uuid4(),
        employee_id=emp_id,
        annual_base_salary=120000.0,
        monthly_allowance=1000.0,
        monthly_deduction=200.0,
        currency="USD",
        revision_number=1,
        effective_from=date(2020, 1, 1),
        is_current=True
    )
    db.add(salary)
    db.commit()
    db.refresh(employee)
    return employee

def test_get_analytics_stats_success(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    create_test_employee(db_session, default_tenant.id, default_department.id, "Alice", "Smith", "alice@test.com")
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/analytics/stats", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["total_employees"] == 1
    assert json_data["active_employees"] == 1
    assert json_data["total_base_salary"] == 120000.0
    assert json_data["avg_base_salary"] == 120000.0

def test_get_analytics_departments_success(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    create_test_employee(db_session, default_tenant.id, default_department.id, "Alice", "Smith", "alice@test.com")
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/analytics/departments", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) == 1
    assert json_data[0]["department"] == "Engineering"
    assert json_data[0]["employee_count"] == 1
    assert json_data[0]["avg_salary"] == 120000.0

def test_get_analytics_countries_success(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    create_test_employee(db_session, default_tenant.id, default_department.id, "Alice", "Smith", "alice@test.com")
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/analytics/countries", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) == 1
    assert json_data[0]["country"] == "United States"
    assert json_data[0]["currency"] == "USD"
    assert json_data[0]["employee_count"] == 1

def test_get_analytics_salary_distribution_success(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    create_test_employee(db_session, default_tenant.id, default_department.id, "Alice", "Smith", "alice@test.com")
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/analytics/salary-distribution", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) > 0
    non_zero_bands = [b for b in json_data if b["employee_count"] > 0]
    assert len(non_zero_bands) == 1
    assert non_zero_bands[0]["band"] == "$100K - $150K"

def test_get_analytics_extreme_salaries_success(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    emp = create_test_employee(db_session, default_tenant.id, default_department.id, "Alice", "Smith", "alice@test.com")
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/analytics/extreme-salaries", headers=headers)
    print("RESPONSE BODY:", response.text)
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data["highest_paid"]) == 1
    assert len(json_data["lowest_paid"]) == 1
    assert json_data["highest_paid"][0]["employee_code"] == emp.employee_code


def test_get_analytics_salary_audit_success(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # Employee 1: High salary (180K), recent revision (June 2026) -> not underpaid, not overdue
    emp1_id = uuid4()
    emp1 = Employee(
        id=emp1_id,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        employee_code="TEST-ALICE",
        first_name="Alice",
        last_name="Smith",
        email="alice@test.com",
        country="United States",
        status=1,
        joining_date=date(2026, 1, 1)
    )
    db_session.add(emp1)
    db_session.add(SalaryRevision(
        id=uuid4(),
        employee_id=emp1_id,
        annual_base_salary=180000.0,
        monthly_allowance=0.0,
        monthly_deduction=0.0,
        currency="USD",
        revision_number=1,
        effective_from=date(2026, 6, 1),
        is_current=True
    ))

    # Employee 2: Low salary (45K), very old revision (Jan 2020) -> underpaid, overdue
    emp2_id = uuid4()
    emp2 = Employee(
        id=emp2_id,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        employee_code="TEST-BOB",
        first_name="Bob",
        last_name="Jones",
        email="bob@test.com",
        country="United States",
        status=1,
        joining_date=date(2020, 1, 1)
    )
    db_session.add(emp2)
    db_session.add(SalaryRevision(
        id=uuid4(),
        employee_id=emp2_id,
        annual_base_salary=45000.0,
        monthly_allowance=0.0,
        monthly_deduction=0.0,
        currency="USD",
        revision_number=1,
        effective_from=date(2020, 1, 1),
        is_current=True
    ))

    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/analytics/salary-audit", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert "underpaid_employees" in json_data
    assert "overdue_reviews" in json_data

    # Bob should be underpaid (Compa Ratio 0.40)
    underpaid_codes = [x["employee_code"] for x in json_data["underpaid_employees"]]
    assert "TEST-BOB" in underpaid_codes
    assert "TEST-ALICE" not in underpaid_codes

    bob_audit = [x for x in json_data["underpaid_employees"] if x["employee_code"] == "TEST-BOB"][0]
    assert bob_audit["compa_ratio"] == 0.4
    assert bob_audit["department_avg"] == 112500.0

    # Bob should also be overdue for review
    overdue_codes = [x["employee_code"] for x in json_data["overdue_reviews"]]
    assert "TEST-BOB" in overdue_codes
    assert "TEST-ALICE" not in overdue_codes

