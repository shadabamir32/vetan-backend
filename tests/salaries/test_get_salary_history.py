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


def test_get_salary_history_success(client: TestClient, db_session: Session, default_tenant: Tenant, default_department: Department) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    emp = create_test_employee(db_session, default_tenant.id, default_department.id, "Sophia", "Brown", "sophia.brown@acme.com")
    
    # Create an additional historical revision
    historical_sal = SalaryRevision(
        id=uuid4(),
        employee_id=emp.id,
        annual_base_salary=90000.0,
        monthly_allowance=900.0,
        monthly_deduction=150.0,
        currency="USD",
        revision_number=2,
        effective_from=date(2022, 1, 1),
        is_current=False
    )
    db_session.add(historical_sal)
    db_session.commit()
    
    response = client.get(f"/api/v1/employees/{emp.id.hex}/salary-revisions", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) == 2
    # Verify sorted by revision_number ascending
    assert json_data[0]["revision_number"] == 1
    assert json_data[1]["revision_number"] == 2


def test_get_salary_history_validation_error(client: TestClient, default_tenant: Tenant) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/employees/invalid-uuid-format/salary-revisions", headers=headers)
    assert response.status_code == 422
    assert "Invalid employee ID format" in response.json()["detail"]


def test_get_salary_history_not_found(client: TestClient, default_tenant: Tenant) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    fake_emp_id = uuid4().hex
    response = client.get(f"/api/v1/employees/{fake_emp_id}/salary-revisions", headers=headers)
    assert response.status_code == 404
    assert "Employee not found" in response.text


def test_get_salary_history_exception(default_tenant: Tenant, db_session: Session, default_department: Department) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    emp = create_test_employee(db_session, default_tenant.id, default_department.id, "Sophia", "Brown", "sophia.brown@acme.com")
    
    with TestClient(app, raise_server_exceptions=False) as c:
        with patch("sqlalchemy.orm.Query.all", side_effect=Exception("Database read error")):
            response = c.get(f"/api/v1/employees/{emp.id.hex}/salary-revisions", headers=headers)
            assert response.status_code == 500
