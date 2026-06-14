import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import patch
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models import Employee, SalaryRevision, Tenant, Department, PayrollRun, PayrollRecord

def test_get_payroll_run_details_success(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # 1. Create a test employee
    emp = Employee(
        id=uuid4(),
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        employee_code="TEST-DETAILS-123",
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        country="United States",
        status=1,
        joining_date=date(2026, 1, 1)
    )
    db_session.add(emp)
    db_session.commit()

    # 2. Create a payroll run
    run = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=6,
        payroll_year=2026,
        status=2,
        run_at=datetime.utcnow()
    )
    db_session.add(run)
    db_session.commit()

    # 3. Create a payroll record for that run and employee
    record = PayrollRecord(
        id=uuid4(),
        payroll_run_id=run.id,
        employee_id=emp.id,
        gross_amount=Decimal("10500.00"),
        deduction_amount=Decimal("500.00"),
        net_amount=Decimal("10000.00"),
        currency="USD",
        created_at=datetime.utcnow()
    )
    db_session.add(record)
    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}
    
    # Get details
    response = client.get(f"/api/v1/payroll/runs/{run.id}", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    
    assert json_data["id"] == str(run.id)
    assert json_data["payroll_month"] == 6
    assert json_data["payroll_year"] == 2026
    assert json_data["total_gross"] == "10500.00"
    assert json_data["total_deduction"] == "500.00"
    assert json_data["total_net"] == "10000.00"
    assert json_data["employee_count"] == 1
    assert json_data["filtered_count"] == 1
    assert json_data["page"] == 1
    assert json_data["limit"] == 20
    assert json_data["pages"] == 1
    
    records = json_data["records"]
    assert len(records) == 1
    rec = records[0]
    assert rec["employee_id"] == str(emp.id)
    assert rec["employee_code"] == "TEST-DETAILS-123"
    assert rec["first_name"] == "Jane"
    assert rec["last_name"] == "Doe"
    assert rec["department_name"] == "Engineering"
    assert rec["gross_amount"] == "10500.00"
    assert rec["deduction_amount"] == "500.00"
    assert rec["net_amount"] == "10000.00"
    assert rec["currency"] == "USD"


def test_get_payroll_run_details_validation_error(
    client: TestClient,
    default_tenant: Tenant
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/payroll/runs/invalid-uuid-format", headers=headers)
    assert response.status_code == 422
    assert "Invalid payroll run ID format" in response.json()["detail"]


def test_get_payroll_run_details_not_found(
    client: TestClient,
    default_tenant: Tenant
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    fake_run_id = str(uuid4())
    response = client.get(f"/api/v1/payroll/runs/{fake_run_id}", headers=headers)
    assert response.status_code == 404
    assert "Payroll run not found" in response.json()["detail"]


def test_get_payroll_run_details_exception(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant
) -> None:
    run = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=6,
        payroll_year=2026,
        status=2,
        run_at=datetime.utcnow()
    )
    db_session.add(run)
    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}
    with patch("sqlalchemy.orm.Query.all", side_effect=Exception("Database connection timeout")):
        response = client.get(f"/api/v1/payroll/runs/{run.id}", headers=headers)
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


def test_get_payroll_run_details_pagination(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # 1. Create a payroll run
    run = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=6,
        payroll_year=2026,
        status=2,
        run_at=datetime.utcnow()
    )
    db_session.add(run)
    db_session.commit()

    # 2. Create 5 employees and 5 payroll records
    employees = []
    for i in range(5):
        emp = Employee(
            id=uuid4(),
            tenant_id=default_tenant.id,
            department_id=default_department.id,
            employee_code=f"PAG-EMP-{i}",
            first_name=f"Emp{i}",
            last_name="Test",
            email=f"emp{i}@example.com",
            country="United States",
            status=1,
            joining_date=date(2026, 1, 1)
        )
        db_session.add(emp)
        employees.append(emp)
    db_session.commit()

    # Create payroll records
    for i, emp in enumerate(employees):
        record = PayrollRecord(
            id=uuid4(),
            payroll_run_id=run.id,
            employee_id=emp.id,
            gross_amount=Decimal("1000.00") * (i + 1),
            deduction_amount=Decimal("100.00"),
            net_amount=(Decimal("1000.00") * (i + 1)) - Decimal("100.00"),
            currency="USD",
            created_at=datetime.utcnow()
        )
        db_session.add(record)
    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}

    # Test page 1 with limit 2
    # Expect: 2 records, page=1, limit=2, pages=3
    # Total gross = 1000 + 2000 + 3000 + 4000 + 5000 = 15000
    # Total deduction = 500
    # Total net = 14500
    response = client.get(f"/api/v1/payroll/runs/{run.id}?page=1&limit=2", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["total_gross"] == "15000.00"
    assert json_data["total_deduction"] == "500.00"
    assert json_data["total_net"] == "14500.00"
    assert json_data["employee_count"] == 5
    assert json_data["filtered_count"] == 5
    assert json_data["page"] == 1
    assert json_data["limit"] == 2
    assert json_data["pages"] == 3
    assert len(json_data["records"]) == 2

    # Test page 3 with limit 2
    # Expect: 1 record, page=3, limit=2, pages=3
    response2 = client.get(f"/api/v1/payroll/runs/{run.id}?page=3&limit=2", headers=headers)
    assert response2.status_code == 200
    json_data2 = response2.json()
    assert json_data2["page"] == 3
    assert json_data2["limit"] == 2
    assert json_data2["pages"] == 3
    assert json_data2["filtered_count"] == 5
    assert len(json_data2["records"]) == 1


def test_get_payroll_run_details_filtering(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # 1. Create a payroll run
    run = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=6,
        payroll_year=2026,
        status=2,
        run_at=datetime.utcnow()
    )
    db_session.add(run)
    db_session.commit()

    # 2. Create another department
    other_dept = Department(
        id=uuid4(),
        tenant_id=default_tenant.id,
        name="Sales"
    )
    db_session.add(other_dept)
    db_session.commit()

    # 3. Create 3 employees with different names, departments, countries
    # Emp 1: Jane Doe, Engineering, US
    emp1 = Employee(
        id=uuid4(),
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        employee_code="FIL-EMP-1",
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        country="United States",
        status=1,
        joining_date=date(2026, 1, 1)
    )
    db_session.add(emp1)

    # Emp 2: John Smith, Sales, UK
    emp2 = Employee(
        id=uuid4(),
        tenant_id=default_tenant.id,
        department_id=other_dept.id,
        employee_code="FIL-EMP-2",
        first_name="John",
        last_name="Smith",
        email="john.smith@example.co.uk",
        country="United Kingdom",
        status=1,
        joining_date=date(2026, 1, 1)
    )
    db_session.add(emp2)

    # Emp 3: Alice Cooper, Engineering, UK
    emp3 = Employee(
        id=uuid4(),
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        employee_code="FIL-EMP-3",
        first_name="Alice",
        last_name="Cooper",
        email="alice.cooper@example.co.uk",
        country="United Kingdom",
        status=1,
        joining_date=date(2026, 1, 1)
    )
    db_session.add(emp3)
    db_session.commit()

    # Create payroll records
    for emp in [emp1, emp2, emp3]:
        record = PayrollRecord(
            id=uuid4(),
            payroll_run_id=run.id,
            employee_id=emp.id,
            gross_amount=Decimal("5000.00"),
            deduction_amount=Decimal("500.00"),
            net_amount=Decimal("4500.00"),
            currency="USD",
            created_at=datetime.utcnow()
        )
        db_session.add(record)
    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}

    # Filter by search = "John" (fuzzy matching first_name/last_name/code/email)
    # Expect: John Smith only (1 record)
    response = client.get(f"/api/v1/payroll/runs/{run.id}?search=John", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["employee_count"] == 3  # Grand total is still 3
    assert data["filtered_count"] == 1  # Filtered count is 1
    assert data["pages"] == 1
    assert len(data["records"]) == 1
    assert data["records"][0]["first_name"] == "John"

    # Filter by department_id = Engineering
    # Expect: Jane Doe and Alice Cooper (2 records)
    response_dept = client.get(f"/api/v1/payroll/runs/{run.id}?department_id={default_department.id}", headers=headers)
    assert response_dept.status_code == 200
    data_dept = response_dept.json()
    assert data_dept["employee_count"] == 3
    assert data_dept["filtered_count"] == 2
    assert len(data_dept["records"]) == 2
    names = {r["first_name"] for r in data_dept["records"]}
    assert names == {"Jane", "Alice"}

    # Filter by country = "United Kingdom"
    # Expect: John Smith and Alice Cooper (2 records)
    response_country = client.get(f"/api/v1/payroll/runs/{run.id}?country=United%20Kingdom", headers=headers)
    assert response_country.status_code == 200
    data_country = response_country.json()
    assert data_country["employee_count"] == 3
    assert data_country["filtered_count"] == 2
    assert len(data_country["records"]) == 2
    names_c = {r["first_name"] for r in data_country["records"]}
    assert names_c == {"John", "Alice"}

    # Combined filter: country = "United Kingdom" AND department_id = Engineering
    # Expect: Alice Cooper only (1 record)
    response_comb = client.get(f"/api/v1/payroll/runs/{run.id}?country=United%20Kingdom&department_id={default_department.id}", headers=headers)
    assert response_comb.status_code == 200
    data_comb = response_comb.json()
    assert data_comb["employee_count"] == 3
    assert data_comb["filtered_count"] == 1
    assert len(data_comb["records"]) == 1
    assert data_comb["records"][0]["first_name"] == "Alice"
