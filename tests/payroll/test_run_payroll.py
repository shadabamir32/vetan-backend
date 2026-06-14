import pytest
import calendar
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models import Employee, SalaryRevision, Tenant, Department, PayrollRun, PayrollRecord
from clients.database import SessionLocal
from routes.payroll import process_payroll_in_background

def create_test_employee(
    db: Session,
    tenant_id: UUID,
    department_id: UUID,
    first_name: str,
    last_name: str,
    email: str,
    annual_base_salary: float,
    monthly_allowance: float,
    monthly_deduction: float,
    joining_date: date,
    status: int = 1,
    termination_date: date = None
) -> Employee:
    emp_id = uuid4()
    employee = Employee(
        id=emp_id,
        tenant_id=tenant_id,
        department_id=department_id,
        employee_code=f"EMP-{first_name.upper()}-{uuid4().hex[:4]}",
        first_name=first_name,
        last_name=last_name,
        email=email,
        country="United States",
        status=status,
        joining_date=joining_date,
        termination_date=termination_date
    )
    db.add(employee)

    salary = SalaryRevision(
        id=uuid4(),
        employee_id=emp_id,
        annual_base_salary=annual_base_salary,
        monthly_allowance=monthly_allowance,
        monthly_deduction=monthly_deduction,
        currency="USD",
        revision_number=1,
        effective_from=joining_date,
        is_current=True
    )
    db.add(salary)
    db.commit()
    db.refresh(employee)
    return employee


def test_run_payroll_success(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # 1. Create a test employee
    emp = create_test_employee(
        db=db_session,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        first_name="Alice",
        last_name="Smith",
        email="alice.smith@example.com",
        annual_base_salary=120000.0,
        monthly_allowance=1000.0,
        monthly_deduction=200.0,
        joining_date=date(2026, 1, 1)
    )

    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {
        "payroll_month": 6,
        "payroll_year": 2026
    }

    # 2. Run payroll - returns the initial Pending (0) run response
    response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
    assert response.status_code == 201
    json_data = response.json()
    assert "id" in json_data
    assert json_data["payroll_month"] == 6
    assert json_data["payroll_year"] == 2026
    assert json_data["status"] == 0  # Starts as Pending (0)

    # 3. TestClient executes background task synchronously before post returns,
    # so we verify in DB that calculations completed and status transitioned to Processed (2)
    run_id = UUID(json_data["id"])
    payroll_run = db_session.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    assert payroll_run is not None
    assert payroll_run.status == 2  # Finishes as Processed (2)
    assert payroll_run.message == "Processed successfully with 1 records."

    records = db_session.query(PayrollRecord).filter(PayrollRecord.payroll_run_id == run_id).all()
    assert len(records) == 1
    rec = records[0]
    assert rec.employee_id == emp.id
    # Calculations: (120000.0 / 12) + 1000.0 = 11000.0 gross
    # 200.0 deduction
    # 10800.0 net
    assert rec.gross_amount == Decimal("11000.00")
    assert rec.deduction_amount == Decimal("200.00")
    assert rec.net_amount == Decimal("10800.00")
    assert rec.currency == "USD"


def test_run_payroll_pending_status(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # Create test employee
    create_test_employee(
        db=db_session,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        first_name="Alice",
        last_name="Smith",
        email="alice.smith@example.com",
        annual_base_salary=120000.0,
        monthly_allowance=1000.0,
        monthly_deduction=200.0,
        joining_date=date(2026, 1, 1)
    )

    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {
        "payroll_month": 6,
        "payroll_year": 2026
    }

    # Patch add_task so the background task is NOT executed, preserving status as Pending (0)
    with patch("fastapi.BackgroundTasks.add_task") as mock_add_task:
        response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
        assert response.status_code == 201
        assert response.json()["status"] == 0
        mock_add_task.assert_called_once()

        run_id = UUID(response.json()["id"])
        payroll_run = db_session.query(PayrollRun).filter(PayrollRun.id == run_id).first()
        assert payroll_run.status == 0


def test_run_payroll_in_progress_status(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    create_test_employee(
        db=db_session,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        first_name="Alice",
        last_name="Smith",
        email="alice.smith@example.com",
        annual_base_salary=120000.0,
        monthly_allowance=1000.0,
        monthly_deduction=200.0,
        joining_date=date(2026, 1, 1)
    )

    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {
        "payroll_month": 6,
        "payroll_year": 2026
    }

    # Custom mock that asserts status is In Progress (1) while processing
    original_monthrange = calendar.monthrange
    def mock_monthrange(year: int, month: int) -> tuple[int, int]:
        db = SessionLocal()
        run = db.query(PayrollRun).filter(PayrollRun.payroll_month == 6, PayrollRun.payroll_year == 2026).first()
        assert run is not None
        assert run.status == 1  # Verify it is set to In Progress (1)
        db.close()
        return original_monthrange(year, month)

    with patch("calendar.monthrange", side_effect=mock_monthrange):
        response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
        assert response.status_code == 201
        
        # Verify it successfully finished as Processed (2)
        run_id = UUID(response.json()["id"])
        payroll_run = db_session.query(PayrollRun).filter(PayrollRun.id == run_id).first()
        assert payroll_run.status == 2


def test_run_payroll_validation_error(
    client: TestClient,
    default_tenant: Tenant
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}

    # Invalid month
    payload_bad_month = {
        "payroll_month": 13,
        "payroll_year": 2026
    }
    response = client.post("/api/v1/payroll/run", json=payload_bad_month, headers=headers)
    assert response.status_code == 422
    assert "Payroll month must be between 1 and 12" in response.text

    # Invalid year
    payload_bad_year = {
        "payroll_month": 6,
        "payroll_year": 1999
    }
    response = client.post("/api/v1/payroll/run", json=payload_bad_year, headers=headers)
    assert response.status_code == 422
    assert "Payroll year must be 2000 or later" in response.text


def test_run_payroll_duplicate_run(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    create_test_employee(
        db=db_session,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        first_name="Bob",
        last_name="Jones",
        email="bob.jones@example.com",
        annual_base_salary=60000.0,
        monthly_allowance=0.0,
        monthly_deduction=0.0,
        joining_date=date(2026, 1, 1)
    )

    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {
        "payroll_month": 6,
        "payroll_year": 2026
    }

    # Run first time
    response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
    assert response.status_code == 201
    
    # Wait, Starlette's TestClient runs background tasks synchronously. So the run is already status 2.
    run = db_session.query(PayrollRun).filter(
        PayrollRun.tenant_id == default_tenant.id,
        PayrollRun.payroll_month == 6,
        PayrollRun.payroll_year == 2026
    ).first()
    assert run is not None
    assert run.status == 2

    # Run second time - should be allowed to re-queue since status is Processed (2)
    response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
    assert response.status_code == 201

    # Manually change the status to In Progress (1) in DB to test blocking
    run.status = 1
    db_session.commit()

    # Try running again - should be blocked with 400 (In Progress)
    response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Payroll run is currently in progress" in response.json()["detail"]

    # Manually change the status to Pending (0) in DB to test blocking
    run.status = 0
    db_session.commit()

    # Try running again - should be blocked with 400 (Pending)
    response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
    assert response.status_code == 400
    assert "Payroll run is already queued and pending" in response.json()["detail"]


def test_run_payroll_no_eligible_employees(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {
        "payroll_month": 6,
        "payroll_year": 2026
    }

    response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
    assert response.status_code == 201  # Successfully queued!
    
    run_id = UUID(response.json()["id"])
    run = db_session.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    assert run.status == 2  # Background task runs and finishes as Processed (2)
    assert run.message == "Processed successfully with 0 records."


def test_run_payroll_exception_during_queue(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    create_test_employee(
        db=db_session,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        first_name="Bob",
        last_name="Jones",
        email="bob.jones@example.com",
        annual_base_salary=60000.0,
        monthly_allowance=0.0,
        monthly_deduction=0.0,
        joining_date=date(2026, 1, 1)
    )

    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {
        "payroll_month": 6,
        "payroll_year": 2026
    }

    with patch("sqlalchemy.orm.Session.commit", side_effect=Exception("Database error")):
        response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
        assert response.status_code == 500
        assert "Database error during payroll queueing" in response.json()["detail"]


def test_run_payroll_retry_success(
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    emp = create_test_employee(
        db=db_session,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        first_name="Alice",
        last_name="Smith",
        email="alice.smith@example.com",
        annual_base_salary=120000.0,
        monthly_allowance=1000.0,
        monthly_deduction=200.0,
        joining_date=date(2026, 1, 1)
    )

    # Seed the pending run
    run = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=6,
        payroll_year=2026,
        status=0,
        run_at=date(2026, 6, 30)
    )
    db_session.add(run)
    db_session.commit()

    # Side effect: first attempt raises Exception, second succeeds
    side_effects = [Exception("Temp DB failure"), (0, 30)]

    with patch("calendar.monthrange", side_effect=side_effects):
        process_payroll_in_background(run.id, default_tenant.id, max_retries=2)

    db_session.refresh(run)
    assert run.status == 2  # Succeeds on retry
    assert run.message == "Processed successfully with 1 records."

    records = db_session.query(PayrollRecord).filter(PayrollRecord.payroll_run_id == run.id).all()
    assert len(records) == 1
    assert records[0].net_amount == Decimal("10800.00")


def test_run_payroll_failed_status(
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    emp = create_test_employee(
        db=db_session,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        first_name="Alice",
        last_name="Smith",
        email="alice.smith@example.com",
        annual_base_salary=120000.0,
        monthly_allowance=1000.0,
        monthly_deduction=200.0,
        joining_date=date(2026, 1, 1)
    )

    # Seed the pending run
    run = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=6,
        payroll_year=2026,
        status=0,
        run_at=date(2026, 6, 30)
    )
    db_session.add(run)
    db_session.commit()

    # Continuously fails
    with patch("calendar.monthrange", side_effect=Exception("Database down")):
        process_payroll_in_background(run.id, default_tenant.id, max_retries=3)

    db_session.refresh(run)
    assert run.status == 4  # Ultimately transitions to Failure (4)
    assert "Failed: Database down" in run.message

    # Ensure no records got committed (atomicity)
    records = db_session.query(PayrollRecord).filter(PayrollRecord.payroll_run_id == run.id).all()
    assert len(records) == 0


def test_run_payroll_requeue_failed_run(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # Create test employee
    create_test_employee(
        db=db_session,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        first_name="Alice",
        last_name="Smith",
        email="alice.smith@example.com",
        annual_base_salary=120000.0,
        monthly_allowance=1000.0,
        monthly_deduction=200.0,
        joining_date=date(2026, 1, 1)
    )

    # Seed a failed run
    run = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=6,
        payroll_year=2026,
        status=4,  # Failure
        run_at=date(2026, 6, 30)
    )
    db_session.add(run)
    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {
        "payroll_month": 6,
        "payroll_year": 2026
    }

    # Request run again: should reset state to Pending (0) and re-queue background task
    response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["status"] == 0
    assert response.json()["id"] == str(run.id)

    db_session.refresh(run)
    assert run.status == 2  # Finishes as Processed (2) after background execution


def test_run_payroll_skipped_employee(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # 1. Create a test employee with a salary revision
    create_test_employee(
        db=db_session,
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        first_name="Alice",
        last_name="Smith",
        email="alice.smith@example.com",
        annual_base_salary=120000.0,
        monthly_allowance=1000.0,
        monthly_deduction=200.0,
        joining_date=date(2026, 1, 1)
    )

    # 2. Create another employee without a salary revision
    emp_no_rev = Employee(
        id=uuid4(),
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        employee_code="EMP-NO-REV",
        first_name="No",
        last_name="Revision",
        email="no.rev@example.com",
        country="United States",
        status=1,
        joining_date=date(2026, 1, 1)
    )
    db_session.add(emp_no_rev)
    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {
        "payroll_month": 6,
        "payroll_year": 2026
    }

    # Run payroll
    response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
    assert response.status_code == 201

    run_id = UUID(response.json()["id"])
    run = db_session.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    assert run.status == 2
    assert "Processed successfully with 1 records" in run.message
    assert "Skipped 1 employees due to missing revisions (Codes: EMP-NO-REV)" in run.message

    records = db_session.query(PayrollRecord).filter(PayrollRecord.payroll_run_id == run_id).all()
    assert len(records) == 1


def test_run_payroll_all_skipped_fails(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    # Create an employee without a salary revision
    emp_no_rev = Employee(
        id=uuid4(),
        tenant_id=default_tenant.id,
        department_id=default_department.id,
        employee_code="EMP-NO-REV",
        first_name="No",
        last_name="Revision",
        email="no.rev@example.com",
        country="United States",
        status=1,
        joining_date=date(2026, 1, 1)
    )
    db_session.add(emp_no_rev)
    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}
    payload = {
        "payroll_month": 6,
        "payroll_year": 2026
    }

    # Run payroll
    response = client.post("/api/v1/payroll/run", json=payload, headers=headers)
    assert response.status_code == 201

    run_id = UUID(response.json()["id"])
    run = db_session.query(PayrollRun).filter(PayrollRun.id == run_id).first()
    assert run.status == 4
    assert "Failed: No eligible employees had active salary revisions" in run.message

    # Ensure no records got committed
    records = db_session.query(PayrollRecord).filter(PayrollRecord.payroll_run_id == run_id).all()
    assert len(records) == 0
