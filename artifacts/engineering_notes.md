# Engineering Design & Architectural Trade-offs

This document outlines the design decisions, architectural patterns, and performance considerations adopted during the engineering of **Vetan**.

---

## 1. Architectural Overview & Tech Stack Decisions

We selected a modern, light-weight, and highly-performant stack for both the backend and frontend to ensure fast development cycles and production-grade reliability.

```text
┌────────────────────────────┐       ┌──────────────────────────────┐
│   React + Vite Frontend    │  HTTP │        FastAPI Backend       │
│  ──────────────────────    │◄─────►│  ──────────────────────────  │
│  TanStack Query            │       │  SQLAlchemy ORM             │
│  Vanilla CSS               │       │  Pydantic Validation        │
│  Recharts                  │       │  SQLite Database            │
└────────────────────────────┘       └──────────────────────────────┘
```

### Backend: FastAPI + SQLAlchemy + SQLite
*   **FastAPI**: Chosen for its high performance (comparable to Go/Node.js), native support for async operations, and automatic OpenAPI schema generation (via Pydantic).
*   **SQLAlchemy ORM**: Provides a clean mapping layer for relational data modeling while allowing low-level SQL optimization (joins, indexing) when needed.
*   **SQLite**: Selected as the database for the MVP assessment sandbox. 
    *   *Trade-off*: While PostgreSQL or MySQL is preferred for highly concurrent multi-write production systems, SQLite's single-file nature makes it ideal for local testing, zero-configuration setups, and fast execution of the automated unit test suite. Standard SQL constraints and indexes ensure migration to larger relational systems is transparent.

### Frontend: React (Vite) + TanStack Query + Recharts
*   **Vite**: Replaced heavier build setups to provide instant Hot Module Replacement (HMR) and optimized, code-split production bundles.
*   **TanStack Query**: Manages caching, query invalidation, background synchronization, and loading states for a smooth Single Page App (SPA) feel.
*   **Recharts**: Provides lightweight, responsive SVG charts (Area and Bar) that integrate seamlessly with React's styling system.
*   **Vanilla CSS**: Used custom CSS custom properties (variables) to implement a dark-mode theme without importing massive UI framework bloat.

---

## 2. Data Modeling & Immutable Auditing (SCD Type 2)

Compensation tracking requires high financial auditing integrity. A common engineering mistake is overwriting an employee's salary when they receive a raise. If done, historical payroll runs for previous months are corrupted because they compute payouts using the new, incorrect rate.

### Slowly Changing Dimensions (SCD Type 2)
To solve this, salary revisions are modeled as **SCD Type 2 immutable records**:
*   Every compensation change creates a new `SalaryRevision` row.
*   The previous revision is closed by setting `is_current = False` and updating its `effective_to` date.
*   The new revision is opened with `is_current = True` and its `effective_from` date set.

```text
[Historical Revision] (is_current: False, effective_to: 2026-03-14)
       │
       ▼ (Promotion/Raise event)
[Current Revision]    (is_current: True,  effective_to: NULL)
```

### Architectural Benefit
When monthly payroll runs are triggered, the engine joins `Employee` with `SalaryRevision` where `SalaryRevision.effective_from <= Date <= SalaryRevision.effective_to` (or current). This guarantees that historical payroll runs remain completely audit-stable and unchanged by future raises.

---

## 3. Scale & Performance Considerations (10,000 Employees)

Handling 10,000 records requires engineering techniques that optimize database queries and network payloads.

### Database Indexing
To ensure $O(1)$ or $O(\log N)$ lookup performance on core queries, indexes are defined on:
*   `Employee.employee_code` and `Employee.email` (for fast direct lookups).
*   Foreign keys: `Employee.department_id` and `Employee.tenant_id`.

### Paginated Endpoints
All listing views (Employee Directory and Payroll Runs) are fully paginated on the backend (default limit: 20). This prevents database memory exhaustion and avoids returning megabytes of JSON over HTTP.

### Multi-Currency Aggregations
Since employees operate in multiple currencies (USD, EUR, INR, GBP, etc.), converting them in SQL queries (using database-level exchange rate tables) increases query complexity and limits scalability. 
*   *Solution*: The analytics endpoints query raw base values and convert them to USD equivalents in python memory using a fast `EXCHANGE_RATES` hash map. This separates database retrieval from exchange rate math.

### Client-Side Export Chunking
Downloading a CSV directory for 10,000 employees can cause HTTP timeouts or browser memory crashes if the backend attempts to serialize all 10,000 records at once.
*   *Solution*: The frontend implements a client-side paginated exporter. It queries the backend in controlled, sequential batches, compiles the data client-side, and generates a CSV blob dynamically. This ensures reliability at scale.

---

## 4. UI Polish & Responsiveness

*   **Responsive Grids**: All grids, chart blocks, and tables collapse to a single-column layout under `1200px` and `900px` screen widths to prevent page horizontal scrolling.
*   **Contrast & Accessibility**: Recharts tooltips are styled using explicit CSS variable mapping (`var(--text-1)` and `var(--text-2)`) to avoid default black text on dark background clipping.
*   **Interactivity**: Table rows link directly to employee details. Tabs maintain active filter states using React state preservation.

---

## 5. Excluded Scope & Security Strategy

To maintain engineering focus on the core HR salary intelligence domain and keep the MVP streamlined, several capabilities were intentionally left out of scope (as detailed in `requirements.md ## 4. Deliberately Out of Scope`).

### Authentication & API Security
*   **Current State**: The API is secured using simple static Tenant API Keys (`X-API-Key` headers) to enforce multi-tenant logical isolation without user authentication complexity.
*   **Security Strategy**: Because compensation data is highly confidential, this internal tool is designed to run securely under a **company private VPN** or VPC.
*   **Authentication Path**: If exposed beyond the VPN, authentication is designed to be handed off to the enterprise's SSO identity provider (OAuth2/OIDC, Okta, Google Workspace, Azure AD) at the gateway or FastAPI middleware level. This leverages established identity infrastructure rather than reinventing authentication mechanisms.

### Other Excluded Features
*   **Employee Self-Service**: The platform exclusively services the HR Manager persona. Self-service portals (viewing payslips, requesting modifications) are excluded to preserve a simple administrative system.
*   **Direct Deactivation & Termination Actions**: In the MVP, employee statuses are managed at the data/seeding level. Active termination workflows and deactivation UI controls are omitted from this release.
*   **Jurisdiction-Specific Tax Engines**: Tax and pension regulations vary widely across countries. To avoid regulatory compliance debt, net pay calculations are simplified using a direct, standard corporate formula: `Net Pay = (Base Salary / 12) + Allowance - Deduction`.
