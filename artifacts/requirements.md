# PeopleComp — Salary & Payroll Management Platform

### Requirements Document v1.0

---

## 1. Goal

Build a web-based salary and payroll management platform to replace ACME Corp's Excel-based HR workflow. The platform will serve as the single source of truth for employee compensation data across approximately 10,000 employees operating in multiple countries and currencies.

The system should enable HR managers to manage employee records, maintain salary history, run payroll calculations, generate compensation reports, and answer compensation-related questions without relying on spreadsheets.

---

## 2. User Persona

### Primary User: HR Manager

The HR Manager is responsible for maintaining employee compensation information and monitoring payroll costs across the organization.

Typical responsibilities include:

* Creating and maintaining employee records
* Managing salary revisions and compensation changes
* Running monthly payroll calculations
* Monitoring payroll expenses across departments and countries
* Exporting payroll and employee reports
* Answering management questions regarding compensation trends

The user is expected to be non-technical and requires a simple, intuitive interface.

---

## 3. Scope & Features

### 3.1 Organization Management

The system is designed to be multi-tenant ready.

For the assessment deployment, a single organization (ACME Corp) will be seeded and available.

Features:

* View organization information
* Organization-level reporting and payroll analytics

---

### 3.2 Employee Management

Manage employee lifecycle and profile information.

Features:

| Feature             | Description                           |
| ------------------- | ------------------------------------- |
| Create Employee     | Add a new employee record             |
| View Employee       | View employee details                 |
| Update Employee     | Modify employee information           |
| Search Employees    | Search by name, email, employee ID    |
| Filter Employees    | Filter by department, country, status |
| Deactivate Employee | Soft-disable employee records         |
| Employee Directory  | Paginated employee listing            |

Employee fields:

* Employee ID
* First Name
* Last Name
* Email
* Department
* Country
* Employment Status
* Joining Date

---

### 3.3 Salary Management

The system maintains a complete history of compensation changes.

Salary records are immutable.

Any compensation change creates a new salary revision.

Features:

| Feature                | Description                          |
| ---------------------- | ------------------------------------ |
| Create Salary Revision | Create a new compensation record     |
| View Salary History    | View all previous revisions          |
| View Current Salary    | View latest active compensation      |
| Multi-Currency Support | Store compensation in local currency |

Salary fields:

* Annual Base Salary
* Allowance
* Deduction
* Currency
* Effective Date

---

### 3.4 Payroll Processing

Generate monthly payroll snapshots using employee compensation data.

Features:

| Feature         | Description                            |
| --------------- | -------------------------------------- |
| Run Payroll     | Generate payroll for a selected month  |
| Payroll History | View historical payroll runs           |
| Payroll Records | View payroll calculations per employee |
| Payroll Summary | View payroll totals and breakdowns     |

Payroll calculation:

Net Payroll = (Annual Base Salary ÷ 12) + Allowance − Deduction

Payroll runs are stored historically to ensure salary changes do not affect previously generated payroll records.

---

### 3.5 Reporting & Analytics

Provide visibility into organizational compensation and payroll spending.

Features:

* Total Employees
* Active Employees
* Total Payroll Cost
* Average Salary
* Highest Paid Employees
* Lowest Paid Employees
* Payroll by Department
* Payroll by Country
* Salary Distribution Analysis

---

### 3.6 Data Export

Export operational data for reporting and finance teams.

Supported exports:

* Employee Directory
* Salary History
* Payroll Summary

Format:

* CSV

---

## 4. Deliberately Out of Scope

The following features are intentionally excluded from v1.0:

| Excluded Feature                                    | Reason                                                                        |
| --------------------------------------------------- | ----------------------------------------------------------------------------- |
| Employee Self-Service Portal                        | Only HR users are supported                                                   |
| Approval Workflows                                  | Compensation changes are directly managed by HR                               |
| Country-Specific Tax Engines                        | Tax calculations vary significantly by jurisdiction and are outside MVP scope |
| Payslip Generation                                  | Payroll summaries are sufficient for the assessment                           |
| Third-Party Authentication (Google, Microsoft, SSO) | Authentication complexity is intentionally avoided                            |
| Email Notifications                                 | Not required for core compensation workflows                                  |
| Bulk Employee Import                                | Seed scripts satisfy initial population requirements                          |
| Advanced Audit Logging                              | Planned for future versions                                                   |
| Native Mobile Application                           | Responsive web application is sufficient                                      |

---

## 5. Technical Architecture

```text
┌────────────────────────────┐       ┌──────────────────────────────┐
│      Next.js Frontend      │  HTTP │        FastAPI Backend       │
│  ──────────────────────    │◄─────►│  ──────────────────────────  │
│  React Query              │       │  SQLAlchemy ORM             │
│  Material UI              │       │  Pydantic Validation        │
│  Recharts                 │       │  SQLite Database            │
└────────────────────────────┘       └──────────────────────────────┘
```

### Backend

* Python 3.12
* FastAPI
* SQLAlchemy
* SQLite
* Alembic
* Pydantic

### Frontend

* Next.js
* TypeScript
* Material UI
* TanStack Query
* Recharts

### API Surface

Organization APIs

* GET /api/organization

Employee APIs

* GET /api/employees
* POST /api/employees
* GET /api/employees/{id}
* PUT /api/employees/{id}

Salary APIs

* POST /api/employees/{id}/salary-revisions
* GET /api/employees/{id}/salary-revisions
* GET /api/employees/{id}/current-salary

Payroll APIs

* POST /api/payroll/run
* GET /api/payroll/runs
* GET /api/payroll/runs/{id}

Reporting APIs

* GET /api/reports/dashboard
* GET /api/reports/departments
* GET /api/reports/countries

Export APIs

* GET /api/exports/employees
* GET /api/exports/payroll
* GET /api/exports/salaries

---

## 6. Seed Data

The seed script generates approximately 10,000 employees across multiple departments and countries.

Generated data includes:

* Employee profiles
* Department assignments
* Country assignments
* Salary revisions
* Multi-currency compensation records

Target dataset:

* 10,000 Employees
* Multiple Departments
* Multiple Countries
* Historical Salary Revisions
* Payroll-ready Compensation Data

The generated dataset should resemble a realistic enterprise workforce and support analytics and reporting use cases.

---

*Document prepared for ACME Salary & Payroll Management Platform — v1.0*
