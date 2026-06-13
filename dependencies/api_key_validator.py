from fastapi.security import APIKeyHeader
from fastapi import Security, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from clients.database import get_db
from models import Tenant

api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API Key (UUID of the active tenant)"
)

def api_key_validator(
    x_api_key: str = Security(api_key_scheme),
    db: Session = Depends(get_db)
) -> UUID:
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: API Key is missing."
        )
    try:
        api_key_uuid = UUID(x_api_key)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: API Key must be a valid UUID."
        )
    
    # Check if tenant exists in the database using the API Key (UUID)
    tenant = db.query(Tenant).filter_by(id=api_key_uuid).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid API Key."
        )
    
    return api_key_uuid
