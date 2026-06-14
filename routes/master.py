from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from clients.database import get_db
from models import Department
from schemas.employee import VALID_COUNTRY_CURRENCY
from dependencies.api_key_validator import api_key_validator

router = APIRouter(prefix="/master", tags=["V1 Master"])


@router.get("/departments")
def get_departments(
    db: Session = Depends(get_db),
    api_key: UUID = Depends(api_key_validator)
):
    """
    List all departments for the active tenant.
    Returns id (UUID) and name for dropdown population.
    """
    departments = (
        db.query(Department)
        .filter(Department.tenant_id == api_key)
        .order_by(Department.name.asc())
        .all()
    )
    return [{"id": str(dept.id), "name": dept.name} for dept in departments]


@router.get("/countries")
def get_countries():
    """
    List all supported countries with their default currency.
    This is static configuration data — no tenant isolation required.
    """
    return [
        {"country": country, "currency": currency}
        for country, currency in VALID_COUNTRY_CURRENCY.items()
    ]
