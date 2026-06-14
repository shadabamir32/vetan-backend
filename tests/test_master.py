import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Tenant, Department

def test_get_departments_success(
    client: TestClient,
    default_tenant: Tenant,
    default_department: Department
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/master/departments", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) == 1
    assert json_data[0]["id"] == str(default_department.id)
    assert json_data[0]["name"] == "Engineering"

def test_get_countries_success(
    client: TestClient,
    default_tenant: Tenant
) -> None:
    headers = {"X-API-Key": str(default_tenant.id)}
    response = client.get("/api/v1/master/countries", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    # Should contain seeded list of countries from routes/master.py
    assert len(json_data) > 0
    # Check shape
    assert "country" in json_data[0]
    assert "currency" in json_data[0]
