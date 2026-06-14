import pytest
from unittest.mock import patch
from datetime import date
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models import Employee, SalaryRevision, Tenant, Department

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


def test_get_employee_success(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # Seed an employee
    emp = create_test_employee(
        db_session, default_tenant.id, default_department.id, 
        "Alice", "Smith", "alice.smith@test.com"
    )
    
    headers = {"X-API-Key": str(default_tenant.id)}
    
    response = client.get(f"/api/v1/employees/{emp.id}", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["id"] == str(emp.id)
    assert json_data["first_name"] == "Alice"
    assert json_data["last_name"] == "Smith"
    assert json_data["email"] == "alice.smith@test.com"
    assert json_data["employee_code"] == "TEST-ALICE"
    assert json_data["department_name"] == "Engineering"
    assert json_data["current_salary"]["annual_base_salary"] == "120000.00"


def test_get_employee_not_found(
    client: TestClient,
    default_tenant: Tenant
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    fake_id = str(uuid4())
    response = client.get(f"/api/v1/employees/{fake_id}", headers=headers)
    assert response.status_code == 404
    assert "Employee not found" in response.json()["detail"]


def test_get_employee_validation_error(
    client: TestClient,
    default_tenant: Tenant
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    # Invalid UUID string format
    response = client.get("/api/v1/employees/invalid-uuid-string", headers=headers)
    assert response.status_code == 422
    assert "Invalid employee ID format" in response.json()["detail"]


def test_get_employee_exception(
    default_tenant: Tenant
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    # Mock default database query call to raise exception
    with TestClient(app, raise_server_exceptions=False) as c:
        with patch("sqlalchemy.orm.Query.first", side_effect=Exception("Database crash")):
            fake_id = str(uuid4())
            response = c.get(f"/api/v1/employees/{fake_id}", headers=headers)
            assert response.status_code == 500
