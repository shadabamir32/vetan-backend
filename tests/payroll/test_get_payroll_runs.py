import pytest
from datetime import datetime
from unittest.mock import patch
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models import Tenant, PayrollRun

def test_get_payroll_runs_success_empty(
    client: TestClient,
    default_tenant: Tenant
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/payroll/runs", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["total"] == 0
    assert json_data["page"] == 1
    assert json_data["limit"] == 20
    assert json_data["pages"] == 1
    assert json_data["data"] == []


def test_get_payroll_runs_success_with_data(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant
) -> None:
    # Seed payroll runs in different states (0: Pending, 1: In Progress, 2: Processed, 4: Failure)
    run1 = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=3,
        payroll_year=2026,
        status=0,  # Pending
        run_at=datetime(2026, 3, 31, 12, 0, 0)
    )
    run2 = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=4,
        payroll_year=2026,
        status=1,  # In Progress
        run_at=datetime(2026, 4, 30, 12, 0, 0)
    )
    run3 = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=5,
        payroll_year=2026,
        status=2,  # Processed
        run_at=datetime(2026, 5, 31, 12, 0, 0)
    )
    run4 = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=6,
        payroll_year=2026,
        status=4,  # Failure
        run_at=datetime(2026, 6, 30, 12, 0, 0)
    )
    db_session.add(run1)
    db_session.add(run2)
    db_session.add(run3)
    db_session.add(run4)
    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/payroll/runs", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["total"] == 4
    assert json_data["page"] == 1
    assert json_data["limit"] == 20
    assert json_data["pages"] == 1

    runs = json_data["data"]
    assert len(runs) == 4

    # Verify descending order by run_at
    assert runs[0]["payroll_month"] == 6
    assert runs[0]["status"] == 4

    assert runs[1]["payroll_month"] == 5
    assert runs[1]["status"] == 2

    assert runs[2]["payroll_month"] == 4
    assert runs[2]["status"] == 1

    assert runs[3]["payroll_month"] == 3
    assert runs[3]["status"] == 0


def test_get_payroll_runs_unauthorized(
    client: TestClient
) -> None:
    # Missing API Key
    response = client.get("/api/v1/payroll/runs")
    assert response.status_code == 401
    assert "API Key is missing" in response.json()["detail"]

    # Invalid UUID format
    headers = {"X-API-Key": "not-a-uuid"}
    response = client.get("/api/v1/payroll/runs", headers=headers)
    assert response.status_code == 401
    assert "API Key must be a valid UUID" in response.json()["detail"]


def test_get_payroll_runs_exception(
    client: TestClient,
    default_tenant: Tenant
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    with patch("sqlalchemy.orm.Query.all", side_effect=Exception("Database connection loss")):
        response = client.get("/api/v1/payroll/runs", headers=headers)
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


def test_get_payroll_runs_filtering(
    client: TestClient,
    db_session: Session,
    default_tenant: Tenant
) -> None:
    # Seed 3 payroll runs
    run1 = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=1,
        payroll_year=2025,
        status=2,  # Processed
        run_at=datetime(2025, 1, 31)
    )
    run2 = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=2,
        payroll_year=2025,
        status=4,  # Failure
        run_at=datetime(2025, 2, 28)
    )
    run3 = PayrollRun(
        id=uuid4(),
        tenant_id=default_tenant.id,
        payroll_month=3,
        payroll_year=2026,
        status=2,  # Processed
        run_at=datetime(2026, 3, 31)
    )
    db_session.add(run1)
    db_session.add(run2)
    db_session.add(run3)
    db_session.commit()

    headers = {"X-API-Key": str(default_tenant.id)}

    # 1. Filter by year = 2025
    response = client.get("/api/v1/payroll/runs?payroll_year=2025", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["data"]) == 2
    assert {r["payroll_month"] for r in data["data"]} == {1, 2}

    # 2. Filter by month = 3
    response_month = client.get("/api/v1/payroll/runs?payroll_month=3", headers=headers)
    assert response_month.status_code == 200
    data_month = response_month.json()
    assert data_month["total"] == 1
    assert data_month["data"][0]["payroll_year"] == 2026

    # 3. Filter by status = 4 (Failure)
    response_status = client.get("/api/v1/payroll/runs?status=4", headers=headers)
    assert response_status.status_code == 200
    data_status = response_status.json()
    assert data_status["total"] == 1
    assert data_status["data"][0]["payroll_month"] == 2

    # 4. Paginate: page 1, limit 2
    response_pag = client.get("/api/v1/payroll/runs?page=1&limit=2", headers=headers)
    assert response_pag.status_code == 200
    data_pag = response_pag.json()
    assert data_pag["total"] == 3
    assert data_pag["pages"] == 2
    assert len(data_pag["data"]) == 2
