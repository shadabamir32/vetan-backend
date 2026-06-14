import pytest
from datetime import date
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import Employee, Tenant, Department, PayrollRun, PayrollRecord, SalaryRevision

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
        joining_date=date(2026, 1, 1)
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
        effective_from=date(2026, 1, 1),
        is_current=True
    )
    db.add(salary)
    db.commit()
    db.refresh(employee)
    return employee


def test_get_payroll_history_empty(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    emp = create_test_employee(
        db_session, default_tenant.id, default_department.id, 
        "Bob", "Builder", "bob.builder@test.com"
    )
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get(f"/api/v1/employees/{emp.id}/payroll-history", headers=headers)
    assert response.status_code == 200
    assert response.json() == []


def test_run_individual_payroll_success(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    emp = create_test_employee(
        db_session, default_tenant.id, default_department.id, 
        "Jane", "Doe", "jane.doe@test.com"
    )
    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {"payroll_month": 6, "payroll_year": 2026}
    
    # Run payroll for June 2026
    response = client.post(f"/api/v1/employees/{emp.id}/run-payroll", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["employee_id"] == str(emp.id)
    assert data["gross_amount"] == "11000.00"  # 120k / 12 + 1000 = 11000
    assert data["deduction_amount"] == "200.00"
    assert data["net_amount"] == "10800.00"
    assert data["payroll_month"] == 6
    assert data["payroll_year"] == 2026

    # Verify payroll history now contains this record
    history_resp = client.get(f"/api/v1/employees/{emp.id}/payroll-history", headers=headers)
    assert history_resp.status_code == 200
    history_data = history_resp.json()
    assert len(history_data) == 1
    assert history_data[0]["payroll_month"] == 6
    assert history_data[0]["payroll_year"] == 2026
    assert history_data[0]["net_amount"] == "10800.00"


def test_run_individual_payroll_not_joined(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # Employee joins in Jun 2026
    emp_id = uuid4()
    emp = Employee(
        id=emp_id,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        employee_code="TEST-LATE",
        first_name="Late",
        last_name="Joiner",
        email="late@test.com",
        country="United States",
        status=1,
        joining_date=date(2026, 6, 1)
    )
    db_session.add(emp)
    
    salary = SalaryRevision(
        id=uuid4(),
        employee_id=emp_id,
        annual_base_salary=120000.0,
        currency="USD",
        revision_number=1,
        effective_from=date(2026, 6, 1),
        is_current=True
    )
    db_session.add(salary)
    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}
    
    # Try running for May 2026 (prior to joining date)
    payload = {"payroll_month": 5, "payroll_year": 2026}
    response = client.post(f"/api/v1/employees/{emp.id}/run-payroll", json=payload, headers=headers)
    assert response.status_code == 400
    assert "had not joined yet" in response.json()["detail"]
