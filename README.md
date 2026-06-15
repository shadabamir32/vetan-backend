# Vetan App

> Multi-tenant salary management and payroll processing API powering global compensation analytics.

Built with **FastAPI** · **SQLAlchemy** · **Pydantic v2** · **Uvicorn**

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
  - [Database Setup](#database-setup)
  - [Running the Server](#running-the-server)
- [API Reference](#api-reference)
  - [Authentication](#authentication)
  - [Health Check](#health-check)
  - [Employees](#employees)
  - [Salaries](#salaries)
  - [Payroll](#payroll)
  - [Analytics](#analytics)
  - [Master Data](#master-data)
- [Database Schema](#database-schema)
- [Multi-Currency Support](#multi-currency-support)
- [Deployment](#deployment)
  - [Docker](#docker)
  - [Docker Compose](#docker-compose)
- [Testing](#testing)
- [License](#license)

---

## Overview

**Vetan** (वेतन — Hindi for "salary") is a backend API service for managing employee compensation across global organizations. It provides a complete suite of endpoints for employee onboarding, salary revision tracking (SCD Type 2), bulk payroll processing, and compensation analytics — all with full multi-tenant isolation.

---

## Features

- **Multi-Tenant Architecture** — Complete data isolation via API key–based tenant resolution
- **Employee Lifecycle Management** — Onboarding, profile updates, status tracking, and termination handling
- **SCD Type 2 Salary Revisions** — Full salary history with effective date tracking and automatic versioning
- **Payroll Processing** — Async bulk payroll runs with chunked processing (1000 employees/chunk), retry logic, and individual payroll generation
- **Compensation Analytics** — Headcount stats, department/country breakdowns, salary band distributions, extreme salary reports, and pay equity audits
- **Multi-Currency Support** — 12 currencies across 15 countries with USD-normalized reporting
- **Background Task Processing** — Non-blocking payroll computation with status tracking (Pending → In Progress → Processed / Failed)
- **Docker-Ready Deployment** — Containerized with Docker Compose, Caddy reverse proxy, and persistent SQLite volumes

---

## Tech Stack

| Layer         | Technology                              |
| ------------- | --------------------------------------- |
| Framework     | FastAPI 0.136+                          |
| ORM           | SQLAlchemy 2.0                          |
| Validation    | Pydantic v2 with email-validator        |
| Server        | Uvicorn (ASGI)                          |
| Database      | SQLite (default) / MySQL (configurable) |
| Containerization | Docker + Docker Compose              |
| Reverse Proxy | Caddy                                   |
| Testing       | pytest + pytest-cov                     |

---

## Architecture

```
vetan-backend/
├── main.py                 # FastAPI app entrypoint & router registration
├── config/
│   └── db.py               # Database connection URL builder (SQLite/MySQL)
├── clients/
│   └── database.py         # SQLAlchemy engine, session factory & get_db dependency
├── models/
│   ├── __init__.py          # Model exports
│   └── models.py            # SQLAlchemy ORM models (Tenant, Department, Employee, etc.)
├── schemas/
│   ├── employee.py          # Pydantic schemas for employee CRUD + validation
│   ├── salary.py            # Pydantic schemas for salary revisions
│   ├── payroll.py           # Pydantic schemas for payroll runs & records
│   └── analytics.py         # Pydantic schemas for analytics responses
├── routes/
│   ├── employees.py         # Employee CRUD + individual payroll endpoints
│   ├── salaries.py          # Salary revision history & creation
│   ├── payroll.py           # Bulk payroll runs, history & details
│   ├── analytics.py         # Compensation analytics & audit endpoints
│   └── master.py            # Reference data (departments, countries)
├── dependencies/
│   └── api_key_validator.py # API key authentication dependency
├── migrations/
│   └── migrations.py        # Schema migration logic
├── seeds/
│   ├── company_seeder_v1.py     # Tenant seed data
│   ├── department_seeder_v1.py  # Department seed data
│   └── employee_seeder_v1.py   # Employee + salary seed data
├── tests/                   # pytest test suite
├── Dockerfile               # Backend container image
├── docker-compose.yml       # Full-stack orchestration
├── Caddyfile                # Reverse proxy configuration
├── requirements.txt         # Python dependencies
└── .env.example             # Environment variable template
```

---

## Getting Started

### Prerequisites

- **Python** 3.11+
- **pip** (or a virtual environment manager)
- **Docker** & **Docker Compose** (optional, for containerized deployment)

### Installation

```bash
# Clone the repository
git clone https://github.com/shadabamir32/vetan-backend.git
cd vetan-backend

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

Copy the example environment file and configure as needed:

```bash
cp .env.example .env
```

#### Environment Variables

| Variable          | Default               | Description                                     |
| ----------------- | --------------------- | ----------------------------------------------- |
| `DB_CONNECTION`   | `sqlite`              | Database driver (`sqlite` or `mysql`)            |
| `DB_DATABASE`     | `salaryapp.db`        | SQLite file path or MySQL database name          |
| `DB_HOST`         | `127.0.0.1`           | MySQL host (only for `mysql` driver)             |
| `DB_PORT`         | `3306`                | MySQL port (only for `mysql` driver)             |
| `DB_USERNAME`     | `root`                | MySQL username (only for `mysql` driver)         |
| `DB_PASSWORD`     | —                     | MySQL password (only for `mysql` driver)         |
| `DB_CHARSET`      | `utf8mb4`             | MySQL charset (only for `mysql` driver)          |
| `VITE_API_URL`    | `http://localhost:8000/api/v1` | Frontend API base URL               |
| `VITE_API_KEY`    | —                     | Tenant API key for frontend                      |
| `VITE_TENANT_NAME`| —                     | Tenant display name for frontend                 |

### Database Setup

Run migrations and seed data:

```bash
# Apply database migrations
python run_migrations.py

# Seed initial data (tenant, departments, employees)
python seed_run.py
```

### Running the Server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive API docs are served at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## API Reference

All endpoints are versioned under `/api/v1`. Requests require an `X-API-Key` header for tenant authentication (see [Authentication](#authentication)).

### Authentication

Every request (except `/api/health` and `/api/v1/master/countries`) must include a valid tenant API key:

```
X-API-Key: <tenant-uuid>
```

The API key corresponds to a `Tenant.id` in the database. All queries are automatically scoped to the authenticated tenant.

---

### Health Check

| Method | Endpoint       | Description                        |
| ------ | -------------- | ---------------------------------- |
| `GET`  | `/api/health`  | Service & database health status   |

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "service": "vetan-backend"
}
```

---

### Employees

| Method | Endpoint                             | Description                                     |
| ------ | ------------------------------------ | ----------------------------------------------- |
| `GET`  | `/api/v1/employees`                  | List employees (paginated, filterable, searchable) |
| `POST` | `/api/v1/employees`                  | Create employee with initial salary revision     |
| `GET`  | `/api/v1/employees/{id}`             | Get employee details                             |
| `PUT`  | `/api/v1/employees/{id}`             | Update employee profile                          |
| `GET`  | `/api/v1/employees/{id}/payroll-history` | Get employee's processed payroll records     |
| `POST` | `/api/v1/employees/{id}/run-payroll` | Run individual payroll for a specific month      |

**Query Parameters** (for `GET /employees`):

| Param           | Type     | Description                                |
| --------------- | -------- | ------------------------------------------ |
| `page`          | `int`    | Page number (default: 1)                   |
| `limit`         | `int`    | Items per page (default: 20)               |
| `search`        | `string` | Fuzzy search on name, email, employee code |
| `department_id` | `uuid`   | Filter by department                       |
| `country`       | `string` | Filter by country                          |
| `status`        | `int`    | Filter by status (1=Active, 0=Inactive)    |

---

### Salaries

| Method | Endpoint                                        | Description                                  |
| ------ | ----------------------------------------------- | -------------------------------------------- |
| `GET`  | `/api/v1/employees/{id}/salary-revisions`       | Get full salary revision history              |
| `GET`  | `/api/v1/employees/{id}/current-salary`         | Get current active salary                     |
| `POST` | `/api/v1/employees/{id}/salary-revisions`       | Create new salary revision (SCD Type 2)       |

Salary revisions follow **Slowly Changing Dimension Type 2** behavior:
- The current revision is marked `is_current = true`
- Creating a new revision automatically closes the previous one (`effective_to` is set, `is_current` flipped to `false`)
- Currency must match the employee's country

---

### Payroll

| Method | Endpoint                     | Description                                        |
| ------ | ---------------------------- | -------------------------------------------------- |
| `POST` | `/api/v1/payroll/run`        | Queue bulk payroll run for a month/year             |
| `GET`  | `/api/v1/payroll/runs`       | List payroll runs (paginated, filterable)           |
| `GET`  | `/api/v1/payroll/runs/{id}`  | Get payroll run details with records & totals       |

**Payroll Run Statuses:**

| Code | Status        | Description                                   |
| ---- | ------------- | --------------------------------------------- |
| `0`  | Pending       | Queued, awaiting processing                   |
| `1`  | In Progress   | Currently computing payroll records            |
| `2`  | Processed     | Successfully completed                         |
| `4`  | Failed        | Processing failed after retries                |

**Payroll Computation Formula:**
```
Gross  = (Annual Base Salary / 12) + Monthly Allowance
Net    = Gross - Monthly Deduction
```

Bulk payroll runs process employees in **chunks of 1,000** with up to **3 automatic retries** on failure. Re-queuing a processed or failed run resets and recomputes all records.

---

### Analytics

| Method | Endpoint                              | Description                                        |
| ------ | ------------------------------------- | -------------------------------------------------- |
| `GET`  | `/api/v1/analytics/stats`             | Overall salary statistics (USD-normalized)          |
| `GET`  | `/api/v1/analytics/departments`       | Headcount & salary breakdown by department          |
| `GET`  | `/api/v1/analytics/countries`         | Headcount & salary breakdown by country             |
| `GET`  | `/api/v1/analytics/salary-distribution` | Employee distribution across salary bands         |
| `GET`  | `/api/v1/analytics/extreme-salaries`  | Top 5 highest & lowest paid employees               |
| `GET`  | `/api/v1/analytics/salary-audit`      | Pay equity (Compa-Ratio < 0.85) & overdue reviews   |

All analytics endpoints normalize salaries to **USD equivalent** using static exchange rates for consistent cross-currency reporting.

---

### Master Data

| Method | Endpoint                        | Description                                |
| ------ | ------------------------------- | ------------------------------------------ |
| `GET`  | `/api/v1/master/departments`    | List tenant departments (for dropdowns)     |
| `GET`  | `/api/v1/master/countries`      | List supported countries with currencies    |

---

## Database Schema

```
┌──────────────┐       ┌──────────────────┐       ┌───────────────────┐
│   tenants    │       │   departments    │       │    employees      │
├──────────────┤       ├──────────────────┤       ├───────────────────┤
│ id (PK, UUID)│──┐    │ id (PK, UUID)    │──┐    │ id (PK, UUID)     │
│ name         │  ├───>│ tenant_id (FK)   │  ├───>│ tenant_id (FK)    │
└──────────────┘  │    │ name             │  │    │ department_id (FK)│
                  │    └──────────────────┘  │    │ employee_code     │
                  │                          │    │ first_name        │
                  │                          │    │ last_name         │
                  │                          │    │ email (unique)    │
                  │                          │    │ country           │
                  │                          │    │ status            │
                  │                          │    │ joining_date      │
                  │                          │    │ termination_date  │
                  │                          │    │ created_at        │
                  │                          │    │ updated_at        │
                  │                          │    └───────────────────┘
                  │                          │             │
                  │    ┌──────────────────┐  │    ┌────────┴──────────┐
                  │    │  payroll_runs    │  │    │ salary_revisions  │
                  │    ├──────────────────┤  │    ├───────────────────┤
                  └───>│ id (PK, UUID)    │  │    │ id (PK, UUID)     │
                       │ tenant_id (FK)   │  │    │ employee_id (FK)  │
                       │ payroll_month    │  │    │ annual_base_salary│
                       │ payroll_year     │  │    │ monthly_allowance │
                       │ status           │  │    │ monthly_deduction │
                       │ run_at           │  │    │ currency          │
                       │ message          │  │    │ revision_number   │
                       └──────────────────┘  │    │ effective_from    │
                                │            │    │ effective_to      │
                       ┌────────┴─────────┐  │    │ is_current        │
                       │ payroll_records  │  │    │ created_at        │
                       ├──────────────────┤  │    └───────────────────┘
                       │ id (PK, UUID)    │  │
                       │ payroll_run_id   │──┘
                       │ employee_id (FK) │
                       │ gross_amount     │
                       │ deduction_amount │
                       │ net_amount       │
                       │ currency         │
                       │ created_at       │
                       └──────────────────┘
```

---

## Multi-Currency Support

Vetan supports 15 countries with 12 currencies. Currency is enforced at the country level — an employee's salary revision must use the currency mapped to their country.

| Country         | Currency |
| --------------- | -------- |
| United States   | USD      |
| United Kingdom  | GBP      |
| Germany         | EUR      |
| India           | INR      |
| Canada          | CAD      |
| Australia       | AUD      |
| France          | EUR      |
| Netherlands     | EUR      |
| Singapore       | SGD      |
| Brazil          | BRL      |
| Mexico          | MXN      |
| Poland          | PLN      |
| Spain           | EUR      |
| Sweden          | SEK      |
| Japan           | JPY      |

Analytics endpoints normalize all salaries to **USD equivalent** using static exchange rates for consistent cross-currency comparisons.

---

## Deployment

### Docker

Build and run the backend container standalone:

```bash
docker build -t vetan-backend .
docker run -p 8000:8000 -v vetan-data:/data vetan-backend
```

### Docker Compose

The full stack includes the backend API, a frontend app, and a Caddy reverse proxy with automatic HTTPS:

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Launch all services
docker compose up -d
```

**Services:**

| Service    | Description                              | Port(s)     |
| ---------- | ---------------------------------------- | ----------- |
| `backend`  | FastAPI + Uvicorn API server             | 8000        |
| `frontend` | Vite-built frontend (served via Caddy)   | 80          |
| `caddy`    | Reverse proxy with auto-TLS              | 80, 443     |

**Production URLs** (configured via Caddyfile):
- Frontend: `https://vetan.alifzone.cloud`
- Backend API: `https://vetan-api.alifzone.cloud`

---

## Testing

Run the test suite with coverage:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=term-missing

# Run specific test modules
pytest tests/test_analytics.py
pytest tests/employees/
pytest tests/salaries/
pytest tests/payroll/
```

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Copyright © 2026 [shadabamir32](https://github.com/shadabamir32)
