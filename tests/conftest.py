import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from uuid import uuid4
from fastapi.testclient import TestClient

import clients.database
from models import Base, Tenant, Department

# 1. Setup in-memory SQLite database
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Patch SessionLocal in clients.database before imports occur
clients.database.SessionLocal = TestingSessionLocal
clients.database.engine = engine

# Now import app and dependencies
from main import app
from clients.database import get_db

# 3. Override get_db dependency in FastAPI app
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def db_session():
    """
    Creates and tears down database tables for each test,
    providing clean isolation.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """
    Provides a FastAPI test client.
    """
    with TestClient(app) as c:
        yield c

@pytest.fixture
def default_tenant(db_session):
    """
    Seeds a default tenant and returns the Tenant object.
    """
    tenant = Tenant(
        id=uuid4(),
        name="ACME"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant

@pytest.fixture
def default_department(db_session, default_tenant):
    """
    Seeds a default department for the default tenant.
    """
    dept = Department(
        id=uuid4(),
        tenant_id=default_tenant.id,
        name="Engineering"
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept
