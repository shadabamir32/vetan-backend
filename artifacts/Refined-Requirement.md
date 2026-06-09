# Vetan — Employee Salary Management Software
## Product Requirements Document

---

## 1. Goal

Build a web-based employee salary management system for ACME Organization's HR team, replacing their current Excel-based workflow. The system must handle **10,000 employees across multiple countries** and enable the HR Manager to:

1. **Manage** salary data efficiently (view, search, filter, edit)
2. **Understand** organizational compensation patterns through analytics and insights
3. **Export** data for reporting and compliance needs

The name "Vetan" (वेतन) means "salary" in Hindi — a nod to the product's core purpose.

---

## 2. User Persona

**Primary User: HR Manager**
- Manages compensation data for the entire organization
- Non-technical — needs an intuitive, Excel-like familiarity but with software reliability
- Needs to answer leadership questions like: *"How do we pay people in India vs. Germany?"*, *"What's our average salary by department?"*, *"How many people earn above ₹20L?"*
- Currently frustrated by Excel limitations: version conflicts, no audit trail, slow with large datasets, error-prone formulas

---

## 3. Scope & Features

### 3.1 Core Features (In Scope — MVP)

#### A. Employee Salary Management (CRUD)
- **View all employees** in a paginated, sortable, searchable table
- **Search & Filter** by: name, employee ID, department, designation, country, salary range
- **View employee detail** — full salary breakdown for a single employee
- **Edit salary** — update an employee's compensation (base salary, bonuses, deductions)
- **Add new employee** — onboard a new employee with salary data
- **Delete employee** — remove an employee record

#### B. Compensation Analytics & Insights Dashboard
This is the "answer questions about how the org pays people" requirement — the differentiator.

- **Summary Cards**: Total payroll, average salary, employee count, country count
- **Salary Distribution**: Histogram/chart showing how salaries are distributed across the org
- **By Department**: Average/median salary breakdown per department
- **By Country**: Average salary comparison across countries (in a common base currency — USD)
- **By Designation/Level**: Pay band analysis
- **Salary Range Analysis**: Min, max, median, percentiles per grouping

#### C. Data Export
- **Export to CSV** — filtered employee list exportable to CSV for offline use / compliance
- Familiar workflow for an HR Manager migrating from Excel

#### D. Seed Data
- Script to generate **10,000 realistic employees** across:
  - 8–10 countries (India, US, UK, Germany, Singapore, Australia, Canada, Japan, Brazil, UAE)
  - 8–10 departments (Engineering, Product, Design, Sales, Marketing, HR, Finance, Legal, Operations, Support)
  - Realistic designations, salary ranges by country, and currency mapping
  - Names appropriate to each country/region

### 3.2 Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| **Page load time** | < 1 second for table views (paginated) |
| **Search/filter** | < 500ms response time |
| **Analytics queries** | < 2 seconds for aggregation queries on 10K rows |
| **UI responsiveness** | Smooth scrolling, no layout shifts, instant filter feedback |
| **Data integrity** | All salary edits validated server-side |
| **Browser support** | Modern browsers (Chrome, Firefox, Edge) |

---

## 4. What We Are Deliberately NOT Building (and Why)

This section is critical. Good engineering is as much about what you leave out as what you include.

### ❌ Authentication & Authorization
**Why not:** This is an internal HR tool assessment. Adding auth (login, roles, permissions) would add significant complexity (JWT/session management, role-based access, password management) without demonstrating salary management capability. In production, this would sit behind the org's SSO (Okta, Azure AD), not a custom auth system.

### ❌ Payroll Processing / Payment Integration
**Why not:** Payroll processing (tax calculations, compliance deductions, bank transfers) is an entirely separate domain with heavy regulatory requirements per country. Our scope is **salary data management**, not payroll execution. Tools like ADP, Gusto, and Deel handle this.

### ❌ Salary Revision History / Audit Trail
**Why not:** While valuable in production, implementing a full temporal data model (versioned salary records, change logs, approval workflows) significantly increases schema complexity and development time. This would be a strong V2 feature. For MVP, we focus on current-state salary management.

### ❌ Multi-Currency Live Conversion
**Why not:** Real-time currency conversion requires external API integration, rate caching, and adds complexity to every aggregation query. Instead, we store salaries in **local currency** and use a **static USD equivalent** for cross-country comparison. This is how most compensation tools handle it — annual compensation planning doesn't need real-time forex rates.

### ❌ Excel/CSV Import
**Why not:** While the org is migrating from Excel, building a robust import system (column mapping, validation, conflict resolution, error handling for 10K rows) is a product in itself. We provide **seed data** for the 10K employees and **CSV export** for the reverse direction. Import would be a strong V2 feature.

### ❌ Notifications / Email Integration
**Why not:** No user-facing workflow in MVP requires notifications. There are no approval flows, no scheduled reports, no alerts. Adding email/notification infrastructure doesn't serve the core use case.

### ❌ Employee Self-Service Portal
**Why not:** The user persona is explicitly the **HR Manager**, not individual employees. A self-service portal (view my salary, request changes) is a different product with different security requirements.

### ❌ AI-Powered Salary Recommendations / Chatbot
**Why not:** While "answer questions" could be interpreted as a natural language interface, the more pragmatic and reliable approach is structured analytics dashboards. AI chatbots for data Q&A are impressive demos but fragile in production. Good charts answer questions faster and more reliably than a chatbot for a known set of questions.

---

## 5. Technical Architecture

### 5.1 Stack Decision

| Layer | Choice | Reasoning |
|-------|--------|-----------|
| **Backend** | Node.js + Express.js | Lightweight, fast to build, excellent for REST APIs, same language as frontend |
| **Database** | SQLite (via Prisma ORM) | Zero-config, file-based, perfect for 10K records, no separate DB server needed. Prisma gives us type-safe queries and easy migrations |
| **Frontend** | React (Vite) | Fast dev server, modern tooling, assessment allows ReactJS |
| **Component Library** | Ant Design (antd) | Rich data table with built-in sort/filter/pagination, chart components, professional look — ideal for data-heavy admin tools |
| **Charts** | Recharts | Lightweight, React-native charting library, great for dashboards |
| **Testing** | Vitest (backend + frontend) | Fast, Vite-native, Jest-compatible API |

### 5.2 Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    React Frontend                    │
│              (Vite + Ant Design + Recharts)          │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Employee  │  │  Analytics   │  │   Export       │  │
│  │ Table     │  │  Dashboard   │  │   Module       │  │
│  └──────────┘  └──────────────┘  └───────────────┘  │
└───────────────────────┬─────────────────────────────┘
                        │ REST API (JSON)
                        ▼
┌─────────────────────────────────────────────────────┐
│                 Express.js Backend                   │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Employee  │  │  Analytics   │  │   Export       │  │
│  │ Routes    │  │  Routes      │  │   Routes       │  │
│  └────┬─────┘  └──────┬───────┘  └───────┬───────┘  │
│       │               │                  │           │
│  ┌────▼───────────────▼──────────────────▼───────┐  │
│  │              Prisma ORM                        │  │
│  └────────────────────┬──────────────────────────┘  │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
               ┌────────────────┐
               │   SQLite DB    │
               │  (vetan.db)    │
               └────────────────┘
```

### 5.3 Database Schema (Planned)

```sql
-- Core employee table — deliberately flat to avoid over-engineering
employees (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  employee_id     TEXT UNIQUE NOT NULL,      -- e.g., "ACME-0001"
  first_name      TEXT NOT NULL,
  last_name       TEXT NOT NULL,
  email           TEXT UNIQUE NOT NULL,
  department      TEXT NOT NULL,             -- denormalized intentionally (see tradeoff note)
  designation     TEXT NOT NULL,
  country         TEXT NOT NULL,
  city            TEXT,
  date_of_joining DATE NOT NULL,
  base_salary     DECIMAL(15,2) NOT NULL,    -- in local currency
  bonus           DECIMAL(15,2) DEFAULT 0,
  deductions      DECIMAL(15,2) DEFAULT 0,
  currency        TEXT NOT NULL,             -- ISO 4217: USD, INR, EUR, etc.
  salary_usd      DECIMAL(15,2) NOT NULL,    -- pre-computed USD equivalent for analytics
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**Tradeoff Note — Denormalized Department/Designation:**
A normalized design would have separate `departments` and `designations` tables with foreign keys. We're deliberately denormalizing because:
1. With 10K rows and ~10 departments, the join cost isn't justified
2. It simplifies the API and seed script significantly
3. HR data in Excel is inherently denormalized — this matches the mental model
4. If we needed referential integrity for departments (e.g., renaming a department cascades), we'd normalize. For read-heavy analytics, denormalization is the right call.

### 5.4 API Design (Planned)

```
GET    /api/employees          — List employees (paginated, filterable, sortable)
GET    /api/employees/:id      — Get single employee
POST   /api/employees          — Create employee
PUT    /api/employees/:id      — Update employee
DELETE /api/employees/:id      — Delete employee
GET    /api/employees/export   — Export filtered list as CSV

GET    /api/analytics/summary          — Total payroll, avg salary, count, etc.
GET    /api/analytics/by-department     — Salary stats grouped by department
GET    /api/analytics/by-country        — Salary stats grouped by country
GET    /api/analytics/by-designation    — Salary stats grouped by designation
GET    /api/analytics/distribution      — Salary distribution histogram data
```

---

## 6. Project Structure (Planned)

```
vetan-backend/
├── docs/
│   ├── REQUIREMENTS.md          ← This document
│   ├── ARCHITECTURE.md          ← Detailed architecture & tradeoffs
│   └── AI-USAGE.md              ← How AI tools were used
├── backend/
│   ├── prisma/
│   │   ├── schema.prisma
│   │   └── seed.js              ← 10K employee seed script
│   ├── src/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── middleware/
│   │   └── index.js
│   ├── tests/
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   ├── tests/
│   └── package.json
└── README.md                    ← Developer onboarding guide
```

---

## 7. Development Phases

| Phase | Scope | Deliverable |
|-------|-------|-------------|
| **Phase 1** | Backend setup, DB schema, seed script, CRUD APIs | Working API with 10K seeded employees |
| **Phase 2** | Frontend — Employee table with search/filter/pagination | Browsable employee list |
| **Phase 3** | Employee detail view, add/edit/delete forms | Full CRUD from UI |
| **Phase 4** | Analytics APIs + Dashboard UI | Compensation insights dashboard |
| **Phase 5** | CSV export, polish, error handling | Production-ready UX |
| **Phase 6** | Tests (unit + integration), documentation | Test suite + docs |
| **Phase 7** | Deployment + video demo | Live deployment |

---

## 8. Success Criteria

The product is successful when an HR Manager can:
1. ✅ Open the app and immediately see a list of all 10,000 employees
2. ✅ Search for "John" and find all Johns in under 500ms
3. ✅ Filter by "Engineering" department + "India" country and see results instantly
4. ✅ Click on an employee and see their full salary details
5. ✅ Edit an employee's salary and see the change reflected
6. ✅ Navigate to a dashboard and see: total payroll, salary by department, salary by country
7. ✅ Export the current filtered view to CSV
8. ✅ Do all of the above without needing a user manual

---

*Document Version: 1.0*  
*Date: June 9, 2026*
