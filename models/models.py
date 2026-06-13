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


class Department(Base):
    __tablename__ = "departments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)

    tenant = relationship("Tenant", back_populates="departments")
    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    department_id = Column(Uuid(as_uuid=True), ForeignKey("departments.id"), nullable=True)

    employee_code = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    country = Column(String, nullable=False)
    status = Column(Integer, nullable=False, default=1)  # 1 = Active, 0 = Inactive
    joining_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="employees")
    department = relationship("Department", back_populates="employees")
    salary_revisions = relationship("SalaryRevision", back_populates="employee", cascade="all, delete-orphan")
    payroll_records = relationship("PayrollRecord", back_populates="employee", cascade="all, delete-orphan")


class SalaryRevision(Base):
    __tablename__ = "salary_revisions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(Uuid(as_uuid=True), ForeignKey("employees.id"), nullable=False)

    annual_base_salary = Column(Numeric(12, 2), nullable=False)
    monthly_allowance = Column(Numeric(12, 2), nullable=False, default=0.0)
    monthly_deduction = Column(Numeric(12, 2), nullable=False, default=0.0)
    currency = Column(String, nullable=False)
    revision_number = Column(Integer, nullable=False, default=1)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="salary_revisions")


class PayrollRun(Base):
    __tablename__ = "payroll_runs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    payroll_month = Column(Integer, nullable=False)
    payroll_year = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False, default=1)  # 1 = Draft, 2 = Processed
    run_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="payroll_runs")
    payroll_records = relationship("PayrollRecord", back_populates="payroll_run", cascade="all, delete-orphan")


class PayrollRecord(Base):
    __tablename__ = "payroll_records"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payroll_run_id = Column(Uuid(as_uuid=True), ForeignKey("payroll_runs.id"), nullable=False)
    employee_id = Column(Uuid(as_uuid=True), ForeignKey("employees.id"), nullable=False)

    gross_amount = Column(Numeric(12, 2), nullable=False)
    deduction_amount = Column(Numeric(12, 2), nullable=False)
    net_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    payroll_run = relationship("PayrollRun", back_populates="payroll_records")
    employee = relationship("Employee", back_populates="payroll_records")
