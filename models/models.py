import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Date, Numeric, Boolean, Uuid
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

    departments = relationship("Department", back_populates="tenant", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="tenant", cascade="all, delete-orphan")
    payroll_runs = relationship("PayrollRun", back_populates="tenant", cascade="all, delete-orphan")
