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
def test_get_employees_success(client: TestClient, db_session: Session, default_tenant: Tenant, default_department: Department) -> None:
    # Seed a couple of employees
    emp1 = create_test_employee(
        db_session, default_tenant.id, default_department.id, 
        "John", "Doe", "john.doe@test.com"
    )
    emp2 = create_test_employee(
        db_session, default_tenant.id, default_department.id, 
        "Jane", "Smith", "jane.smith@test.com"
    )
    
    headers = {"X-API-Key": str(default_tenant.id)}
    
    # Check simple retrieval
    response = client.get("/api/v1/employees", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["total"] == 2
    assert len(json_data["data"]) == 2
    
    # Check filtering by department using non-hyphenated UUID string
    non_hyphenated_dept = default_department.id.hex
    response_filter = client.get(f"/api/v1/employees?department_id={non_hyphenated_dept}", headers=headers)
    assert response_filter.status_code == 200
    assert response_filter.json()["total"] == 2

    # Check search functionality
    response_search = client.get("/api/v1/employees?search=Jane", headers=headers)
    assert response_search.status_code == 200
    assert response_search.json()["total"] == 1
    assert response_search.json()["data"][0]["first_name"] == "Jane"

# 2. VALIDATION ERROR TEST CASE
def test_get_employees_validation_error(client: TestClient, default_tenant: Tenant) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    
    # 422 Unprocessable Entity due to invalid limit value (must be >= 1)
    response = client.get("/api/v1/employees?limit=0", headers=headers)
    assert response.status_code == 422
    
    # 422 Unprocessable Entity due to invalid non-UUID department_id format
    response_uuid = client.get("/api/v1/employees?department_id=invalid-uuid-format", headers=headers)
    assert response_uuid.status_code == 422
    assert "Invalid department_id format" in response_uuid.json()["detail"]

# 3. EXCEPTION TEST CASE (500 Internal Server Error)
def test_get_employees_exception(default_tenant: Tenant) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    
    # Create a TestClient with raise_server_exceptions=False to assert on HTTP 500 response
    with TestClient(app, raise_server_exceptions=False) as c:
        # Mock the db query count to throw an exception to simulate DB crash
        with patch("sqlalchemy.orm.Query.count", side_effect=Exception("Database connection failure")):
            response = c.get("/api/v1/employees", headers=headers)
            assert response.status_code == 500
            assert "Internal Server Error" in response.text
