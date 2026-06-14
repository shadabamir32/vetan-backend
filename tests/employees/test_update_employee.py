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

# 1. SUCCESS TEST CASE
def test_update_employee_success(client: TestClient, db_session: Session, default_tenant: Tenant, default_department: Department) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    
    # Create an employee
    emp = create_test_employee(
        db_session, default_tenant.id, default_department.id, 
        "Sophia", "Brown", "sophia.brown@acme.com"
    )
    
    # We update the employee, specifying the department ID as a non-hyphenated UUID string
    payload = {
        "first_name": "Sophia",
        "last_name": "Browns",
        "email": "sophia.brown2@acme.com",
        "country": "United States",
        "department_id": default_department.id.hex, # non-hyphenated UUID
        "status": 0,
        "joining_date": "2020-06-14",
        "termination_date": "2026-06-14"
    }
    
    # We can pass non-hyphenated UUID string in path too
    response = client.put(f"/api/v1/employees/{emp.id.hex}", json=payload, headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["first_name"] == "Sophia"
    assert json_data["last_name"] == "Browns"
    assert json_data["email"] == "sophia.brown2@acme.com"
    assert json_data["department_id"] == str(default_department.id)
    assert json_data["status"] == 0
    assert json_data["termination_date"] == "2026-06-14"

# 2. VALIDATION ERROR TEST CASES
def test_update_employee_validation_errors(client: TestClient, db_session: Session, default_tenant: Tenant, default_department: Department) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    
    # Create two employees
    emp1 = create_test_employee(
        db_session, default_tenant.id, default_department.id, 
        "Sophia", "Brown", "sophia.brown@acme.com"
    )
    emp2 = create_test_employee(
        db_session, default_tenant.id, default_department.id, 
        "Jane", "Smith", "jane.smith@acme.com"
    )
    
    # Validation Failure A: Duplicate email
    payload_dup = {
        "email": "jane.smith@acme.com" # Already in use by emp2
    }
    response_dup = client.put(f"/api/v1/employees/{emp1.id.hex}", json=payload_dup, headers=headers)
    assert response_dup.status_code == 422
    assert "Email is already in use by another employee" in response_dup.text

    # Validation Failure B: Non-existent department UUID
    fake_dept_id = uuid4().hex
    payload_fake_dept = {
        "department_id": fake_dept_id
    }
    response_fake = client.put(f"/api/v1/employees/{emp1.id.hex}", json=payload_fake_dept, headers=headers)
    assert response_fake.status_code == 422
    assert "Department does not exist" in response_fake.text

# 3. NOT FOUND TEST CASE (404 Error)
def test_update_employee_not_found(client: TestClient, default_tenant: Tenant) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    fake_emp_id = uuid4().hex
    
    payload = {
        "first_name": "Ghost"
    }
    response = client.put(f"/api/v1/employees/{fake_emp_id}", json=payload, headers=headers)
    assert response.status_code == 404
    assert "Employee not found" in response.text

# 4. EXCEPTION TEST CASE (500 Internal Server Error)
def test_update_employee_exception(default_tenant: Tenant, default_department: Department, db_session: Session) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    
    # Create an employee
    emp = create_test_employee(
        db_session, default_tenant.id, default_department.id, 
        "Sophia", "Brown", "sophia.brown@acme.com"
    )
    
    payload = {
        "first_name": "Error"
    }
    
    with TestClient(app, raise_server_exceptions=False) as c:
        # Mock Session.commit to raise an exception simulating database crash on save
        with patch("sqlalchemy.orm.Session.commit", side_effect=Exception("DB write failure")):
            response = c.put(f"/api/v1/employees/{emp.id.hex}", json=payload, headers=headers)
            assert response.status_code == 500
            assert "Database error during update" in response.json()["detail"]
