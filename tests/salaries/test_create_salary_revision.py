import pytest
from unittest.mock import patch
from datetime import date
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from models import Employee, SalaryRevision, Tenant, Department

def create_test_employee(db: Session, tenant_id: UUID, department_id: UUID, first_name: str, last_name: str, email: str) -> Employee:
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
        annual_base_salary=100000.0,
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


def test_create_salary_revision_success(client: TestClient, db_session: Session, default_tenant: Tenant, default_department: Department) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    emp = create_test_employee(db_session, default_tenant.id, default_department.id, "Sophia", "Brown", "sophia.brown@acme.com")
    
    # New effective date is after current effective date (2020-01-01)
    payload = {
        "annual_base_salary": 115000.0,
        "monthly_allowance": 1200.0,
        "monthly_deduction": 250.0,
        "currency": "USD",
        "effective_from": "2021-01-01"
    }
    
    response = client.post(f"/api/v1/employees/{emp.id.hex}/salary-revisions", json=payload, headers=headers)
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["annual_base_salary"] == "115000.00"
    assert json_data["revision_number"] == 2
    assert json_data["is_current"] is True
    assert json_data["effective_from"] == "2021-01-01"
    
    # Check that previous revision was closed
    old_revision = db_session.query(SalaryRevision).filter(SalaryRevision.employee_id == emp.id, SalaryRevision.revision_number == 1).first()
    assert old_revision.is_current is False
    assert old_revision.effective_to == date(2021, 1, 1)


def test_create_salary_revision_validation_errors(client: TestClient, db_session: Session, default_tenant: Tenant, default_department: Department) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    emp = create_test_employee(db_session, default_tenant.id, default_department.id, "Sophia", "Brown", "sophia.brown@acme.com")
    
    # Validation Failure A: Currency mismatch (US employee expects USD)
    payload_currency = {
        "annual_base_salary": 110000.0,
        "currency": "EUR",
        "effective_from": "2021-01-01"
    }
    response_curr = client.post(f"/api/v1/employees/{emp.id.hex}/salary-revisions", json=payload_currency, headers=headers)
    assert response_curr.status_code == 422
    assert "Currency 'EUR' does not match country 'United States'" in response_curr.text

    # Validation Failure B: Negative allowance
    payload_neg = {
        "annual_base_salary": 110000.0,
        "monthly_allowance": -50.0,
        "currency": "USD",
        "effective_from": "2021-01-01"
    }
    response_neg = client.post(f"/api/v1/employees/{emp.id.hex}/salary-revisions", json=payload_neg, headers=headers)
    assert response_neg.status_code == 422
    assert "Monthly allowance cannot be negative" in response_neg.text

    # Validation Failure C: Effective date equal to or before current revision's effective date
    payload_date = {
        "annual_base_salary": 110000.0,
        "currency": "USD",
        "effective_from": "2020-01-01" # equal to current's effective_from (2020-01-01)
    }
    response_date = client.post(f"/api/v1/employees/{emp.id.hex}/salary-revisions", json=payload_date, headers=headers)
    assert response_date.status_code == 422
    assert "New effective date (2020-01-01) must be after" in response_date.json()["detail"]


def test_create_salary_revision_not_found(client: TestClient, default_tenant: Tenant) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    fake_emp_id = uuid4().hex
    payload = {
        "annual_base_salary": 110000.0,
        "currency": "USD",
        "effective_from": "2021-01-01"
    }
    response = client.post(f"/api/v1/employees/{fake_emp_id}/salary-revisions", json=payload, headers=headers)
    assert response.status_code == 404
    assert "Employee not found" in response.text


def test_create_salary_revision_exception(default_tenant: Tenant, default_department: Department, db_session: Session) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    emp = create_test_employee(db_session, default_tenant.id, default_department.id, "Sophia", "Brown", "sophia.brown@acme.com")
    
    payload = {
        "annual_base_salary": 110000.0,
        "currency": "USD",
        "effective_from": "2021-01-01"
    }
    
    with TestClient(app, raise_server_exceptions=False) as c:
        # Mock Session.commit to raise an exception simulating database crash
        with patch("sqlalchemy.orm.Session.commit", side_effect=Exception("DB write failure")):
            response = c.post(f"/api/v1/employees/{emp.id.hex}/salary-revisions", json=payload, headers=headers)
            assert response.status_code == 500
            assert "Database error during salary revision creation" in response.json()["detail"]
