import pytest
from unittest.mock import patch
from datetime import date
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from models import Employee, SalaryRevision, Tenant, Department

# 1. SUCCESS TEST CASE
def test_create_employee_success(client: TestClient, db_session: Session, default_tenant: Tenant, default_department: Department) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    
    payload = {
        "first_name": "Sophia",
        "last_name": "Brown",
        "email": "sophia.brown@acme.com",
        "country": "United States",
        "department_id": default_department.id.hex, # non-hyphenated UUID
        "annual_base_salary": 90000.0,
        "monthly_allowance": 1000.0,
        "monthly_deduction": 200.0,
        "currency": "USD",
        "status": 1,
        "joining_date": "2020-06-14"
    }
    
    response = client.post("/api/v1/employees", json=payload, headers=headers)
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["first_name"] == "Sophia"
    assert json_data["last_name"] == "Brown"
    assert json_data["email"] == "sophia.brown@acme.com"
    assert json_data["department_id"] == str(default_department.id) # returns standard hyphenated UUID
    
    # Assert DB records were created
    emp = db_session.query(Employee).filter_by(email="sophia.brown@acme.com").first()
    assert emp is not None
    assert len(emp.salary_revisions) == 1
    assert emp.salary_revisions[0].annual_base_salary == 90000.0

# 2. VALIDATION ERROR TEST CASES
def test_create_employee_validation_errors(client: TestClient, db_session: Session, default_tenant: Tenant, default_department: Department) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    
    # Validation Failure A: Duplicate email
    # Let's seed an employee first
    existing_emp = Employee(
        id=uuid4(),
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        employee_code="ACME-EXISTING",
        first_name="Existing",
        last_name="User",
        email="existing@acme.com",
        country="United States",
        status=1,
        joining_date=date(2020, 1, 1)
    )
    db_session.add(existing_emp)
    db_session.commit()

    payload_duplicate_email = {
        "first_name": "New",
        "last_name": "User",
        "email": "existing@acme.com", # Duplicate
        "country": "United States",
        "department_id": default_department.id.hex,
        "annual_base_salary": 80000.0,
        "currency": "USD",
        "joining_date": "2020-06-14"
    }
    response_dup = client.post("/api/v1/employees", json=payload_duplicate_email, headers=headers)
    assert response_dup.status_code == 422
    assert "Email is already registered" in response_dup.text

    # Validation Failure B: Country/currency mismatch
    payload_mismatch = {
        "first_name": "Mismatched",
        "last_name": "User",
        "email": "mismatched@acme.com",
        "country": "United States",
        "currency": "EUR", # Should be USD for US
        "annual_base_salary": 80000.0,
        "joining_date": "2020-06-14"
    }
    response_mismatch = client.post("/api/v1/employees", json=payload_mismatch, headers=headers)
    assert response_mismatch.status_code == 422
    assert "Currency 'EUR' does not match country 'United States'" in response_mismatch.text

    # Validation Failure C: Non-existent department UUID
    fake_dept_id = uuid4().hex
    payload_fake_dept = {
        "first_name": "Fake",
        "last_name": "Dept",
        "email": "fake.dept@acme.com",
        "country": "United States",
        "department_id": fake_dept_id, # Valid UUID string, but does not exist in DB
        "annual_base_salary": 80000.0,
        "currency": "USD",
        "joining_date": "2020-06-14"
    }
    response_fake_dept = client.post("/api/v1/employees", json=payload_fake_dept, headers=headers)
    assert response_fake_dept.status_code == 422
    assert "Department does not exist" in response_fake_dept.text

# 3. EXCEPTION TEST CASE (500 Internal Server Error)
def test_create_employee_exception(default_tenant: Tenant, default_department: Department) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {
        "first_name": "Error",
        "last_name": "User",
        "email": "error.user@acme.com",
        "country": "United States",
        "department_id": default_department.id.hex,
        "annual_base_salary": 90000.0,
        "currency": "USD",
        "joining_date": "2020-06-14"
    }
    
    with TestClient(app, raise_server_exceptions=False) as c:
        # Mock Session.commit to raise an exception simulating database crash on save
        with patch("sqlalchemy.orm.Session.commit", side_effect=Exception("DB write failure")):
            response = c.post("/api/v1/employees", json=payload, headers=headers)
            assert response.status_code == 500
            assert "Database error during creation" in response.json()["detail"]
