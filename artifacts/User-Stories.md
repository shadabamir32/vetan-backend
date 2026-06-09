# User Stories — Vetan Phase 1 MVP

## Overview

This document captures the Phase 1 user stories for the Vetan Employee Salary Management System, aligned with the [REQUIREMENTS.md](./REQUIREMENTS.md).

### Story Point Scale (Fibonacci)

| Points | Meaning |
|--------|---------|
| **1** | Trivial — simple config or copy change |
| **2** | Small — straightforward, well-understood work |
| **3** | Medium — moderate complexity, clear approach |
| **5** | Large — significant effort, some unknowns |
| **8** | Very Large — complex, cross-cutting, or multiple components |
| **13** | Epic-level — should be broken down further if possible |

### Priority

| Label | Meaning |
|-------|---------|
| **P0** | Must have — MVP is incomplete without this |
| **P1** | Should have — important for usability but MVP can function without it |
| **P2** | Nice to have — polish and enhancement |

### Primary Persona

**HR Manager** — Responsible for maintaining employee salary information, reviewing compensation data, and generating insights about how the organization pays employees across departments and countries.

---

# Epic 1: Employee Management

## US-001: View Employee Directory

**Priority:** P0 · **Story Points:** 5

**As an** HR Manager,
**I want to** view a paginated list of all employees,
**So that** I can browse employee records efficiently without the application becoming slow.

### Acceptance Criteria

- [ ] Employee list displays columns: Employee ID, Name, Email, Department, Designation, Country, Base Salary (with currency), Salary (USD)
- [ ] Results are server-side paginated with a default page size of 20
- [ ] Page size can be changed (20, 50, 100)
- [ ] Total employee count is displayed (e.g., "Showing 1–20 of 10,000 employees")
- [ ] Default sorting is by employee ID ascending
- [ ] Table loads in under 1 second for any page
- [ ] Empty state is handled gracefully

---

## US-002: Search Employees

**Priority:** P0 · **Story Points:** 3

**As an** HR Manager,
**I want to** search employees by name, employee ID, or email,
**So that** I can quickly locate a specific employee's record.

### Acceptance Criteria

- [ ] A single search input is visible above the employee table
- [ ] Search is case-insensitive
- [ ] Partial matches are supported (e.g., "Joh" matches "John")
- [ ] Search queries are debounced (300ms) to avoid excessive API calls
- [ ] Results update without full page refresh
- [ ] Search results return within 500ms for 10,000 employees
- [ ] Search can be combined with active filters (US-003)
- [ ] Clearing the search field restores the full employee list

---

## US-003: Filter Employees

**Priority:** P0 · **Story Points:** 5

**As an** HR Manager,
**I want to** filter employees by department, designation, country, and salary range,
**So that** I can focus on relevant employee groups for analysis.

### Acceptance Criteria

- [ ] Filter options are available for: Department (multi-select), Designation (multi-select), Country (multi-select), Salary range (min/max in USD)
- [ ] Filter options are populated dynamically from actual data
- [ ] Multiple filters can be applied simultaneously (AND logic)
- [ ] Active filter count/tags are visible
- [ ] A "Clear All Filters" action is available
- [ ] Filtered employee count updates immediately (e.g., "Showing 1–20 of 342 employees")
- [ ] Filters can be combined with search (US-002)
- [ ] Pagination resets to page 1 when filters change

---

## US-004: Sort Employee Table

**Priority:** P1 · **Story Points:** 2

**As an** HR Manager,
**I want to** sort the employee table by any column,
**So that** I can quickly identify highest/lowest paid employees or organize by department.

### Acceptance Criteria

- [ ] Columns sortable: Employee ID, Name, Department, Designation, Country, Base Salary, Salary (USD)
- [ ] Clicking a column header toggles ascending → descending → default
- [ ] Sort indicator (arrow) is visible on the active sort column
- [ ] Sort is performed server-side (not just the current page)
- [ ] Sort state is preserved when changing pages

---

## US-005: View Employee Details

**Priority:** P0 · **Story Points:** 3

**As an** HR Manager,
**I want to** view detailed information for a single employee,
**So that** I can review their full salary breakdown and organizational info.

### Acceptance Criteria

- [ ] Clicking an employee row or a "View" action opens the employee detail view
- [ ] Detail view displays: Employee ID, First Name, Last Name, Email, Department, Designation, Country, City, Date of Joining
- [ ] Salary section displays: Base Salary (in local currency with currency code), Bonus, Deductions, Net Salary (computed: base + bonus − deductions), Salary in USD equivalent
- [ ] Navigation back to the employee list preserves previous search/filter/page state
- [ ] An "Edit" action is accessible from the detail view

---

## US-006: Add New Employee

**Priority:** P0 · **Story Points:** 5

**As an** HR Manager,
**I want to** add a new employee with their salary information,
**So that** new hires are captured in the system immediately.

### Acceptance Criteria

- [ ] An "Add Employee" button is prominently visible on the employee list page
- [ ] A form collects: First Name (required), Last Name (required), Email (required, unique, validated format), Department (required, dropdown), Designation (required, dropdown), Country (required, dropdown), City (optional), Date of Joining (required, date picker), Base Salary (required, positive number), Bonus (optional, defaults to 0), Deductions (optional, defaults to 0), Currency (auto-set based on country selection)
- [ ] Employee ID is auto-generated (e.g., "ACME-10001")
- [ ] Salary USD equivalent is auto-computed using static exchange rates
- [ ] Server-side validation returns clear error messages
- [ ] Duplicate email is rejected with a user-friendly message
- [ ] On success, user is redirected to the new employee's detail view
- [ ] Success confirmation is shown (toast/notification)

---

## US-007: Edit Employee Information

**Priority:** P0 · **Story Points:** 5

**As an** HR Manager,
**I want to** update an employee's salary and organizational information,
**So that** compensation records remain accurate and current.

### Acceptance Criteria

- [ ] Edit is accessible from the employee detail view and from a table row action
- [ ] Editable fields: First Name, Last Name, Email, Department, Designation, Country, City, Base Salary, Bonus, Deductions
- [ ] Employee ID and Date of Joining are read-only (not editable after creation)
- [ ] Currency updates automatically when country changes
- [ ] Salary USD equivalent is recomputed on save
- [ ] Validation prevents: negative salary values, empty required fields, duplicate email
- [ ] `updated_at` timestamp is recorded automatically
- [ ] On success, user returns to the updated detail view with a confirmation message
- [ ] Form pre-populates with current values

---

## US-008: Delete Employee

**Priority:** P1 · **Story Points:** 2

**As an** HR Manager,
**I want to** remove an employee record from the system,
**So that** separated employees no longer appear in active lists and analytics.

### Acceptance Criteria

- [ ] Delete action is accessible from the employee detail view and table row action
- [ ] A confirmation dialog is shown before deletion ("Are you sure you want to delete {name}? This action cannot be undone.")
- [ ] On confirmation, the employee record is permanently deleted
- [ ] User is redirected to the employee list after successful deletion
- [ ] Success confirmation is shown
- [ ] Analytics data updates to reflect the deletion

---

# Epic 2: Compensation Analytics

## US-009: View Compensation Summary Dashboard

**Priority:** P0 · **Story Points:** 5

**As an** HR Manager,
**I want to** view key compensation metrics at a glance,
**So that** I can quickly understand the organization's overall salary position.

### Acceptance Criteria

- [ ] Dashboard is accessible from the main navigation
- [ ] Summary cards display: Total Employees, Total Annual Payroll (USD), Average Salary (USD), Median Salary (USD), Number of Countries, Number of Departments
- [ ] All monetary values are formatted with currency symbols and thousand separators
- [ ] Dashboard loads within 2 seconds
- [ ] Data reflects the current state of the database (not cached stale data)

---

## US-010: Analyze Salaries by Department

**Priority:** P0 · **Story Points:** 5

**As an** HR Manager,
**I want to** compare compensation across departments,
**So that** I can identify departmental salary trends and potential disparities.

### Acceptance Criteria

- [ ] A bar or horizontal bar chart displays average salary (USD) per department
- [ ] Accompanying table shows: Department, Employee Count, Average Salary, Median Salary, Min Salary, Max Salary, Total Spend
- [ ] Chart and table are sorted by average salary descending (default)
- [ ] Clicking a department row navigates/filters to the employee list for that department
- [ ] All values are in USD for cross-department comparability

---

## US-011: Analyze Salaries by Country

**Priority:** P0 · **Story Points:** 5

**As an** HR Manager,
**I want to** compare compensation across countries,
**So that** I can identify regional salary patterns and ensure competitive pay.

### Acceptance Criteria

- [ ] A chart displays average salary (USD) per country
- [ ] Accompanying table shows: Country, Currency, Employee Count, Average Salary (USD), Median Salary (USD), Min, Max, Total Spend (USD)
- [ ] Results can be sorted by any column
- [ ] All values normalized to USD for fair comparison
- [ ] Clicking a country navigates/filters to the employee list for that country

---

## US-012: Analyze Salaries by Designation

**Priority:** P1 · **Story Points:** 3

**As an** HR Manager,
**I want to** compare compensation across designations/levels,
**So that** I can understand pay band distribution and identify outliers.

### Acceptance Criteria

- [ ] Chart displays average salary (USD) per designation
- [ ] Table shows: Designation, Employee Count, Average Salary, Median Salary, Min, Max
- [ ] Results sortable by any column

---

## US-013: View Salary Distribution

**Priority:** P0 · **Story Points:** 5

**As an** HR Manager,
**I want to** visualize salary distribution across the organization,
**So that** I can understand the compensation spread and identify clusters or outliers.

### Acceptance Criteria

- [ ] A histogram chart displays salary distribution in USD
- [ ] Salary ranges are automatically grouped into meaningful bands (e.g., $0–30K, $30K–60K, $60K–90K, etc.)
- [ ] Each band shows the employee count
- [ ] The chart clearly shows the shape of the distribution (normal, skewed, bimodal, etc.)
- [ ] Hovering over a bar shows the exact count and salary range

---

# Epic 3: Data Export

## US-014: Export Employee Data to CSV

**Priority:** P1 · **Story Points:** 3

**As an** HR Manager,
**I want to** export the current employee list (with active filters) to CSV,
**So that** I can share data with leadership or use it in external tools like Excel.

### Acceptance Criteria

- [ ] An "Export CSV" button is visible on the employee list page
- [ ] The export respects current search, filter, and sort state
- [ ] CSV includes all employee columns: Employee ID, First Name, Last Name, Email, Department, Designation, Country, City, Date of Joining, Base Salary, Bonus, Deductions, Currency, Salary USD
- [ ] CSV includes a header row
- [ ] File is named descriptively (e.g., `vetan-employees-2026-06-09.csv`)
- [ ] For unfiltered export of 10,000 employees, download completes within 5 seconds
- [ ] File downloads automatically via the browser

---

# Epic 4: Data Initialization

## US-015: Seed Employee Data

**Priority:** P0 · **Story Points:** 8

**As a** Developer,
**I want to** generate 10,000 realistic employee records via a seed script,
**So that** the application can be demonstrated and tested at production-like scale.

### Acceptance Criteria

- [ ] Script generates exactly 10,000 employee records
- [ ] Employees are distributed across 8–10 countries: India, USA, UK, Germany, Singapore, Australia, Canada, Japan, Brazil, UAE
- [ ] Employees are distributed across 8–10 departments: Engineering, Product, Design, Sales, Marketing, HR, Finance, Legal, Operations, Support
- [ ] Salary ranges are realistic per country (e.g., India: ₹5L–₹50L, USA: $40K–$250K)
- [ ] Correct currency is assigned per country (INR, USD, GBP, EUR, SGD, AUD, CAD, JPY, BRL, AED)
- [ ] USD equivalent is pre-computed using static exchange rates
- [ ] Names are realistic and varied
- [ ] Email addresses follow a consistent pattern (e.g., `firstname.lastname@acme.com`) and are unique
- [ ] Employee IDs follow a sequential pattern (ACME-0001 through ACME-10000)
- [ ] Script is idempotent (can be re-run safely — clears and re-seeds)
- [ ] Script completes in under 60 seconds

---

# Epic 5: Non-Functional Requirements

## US-016: Fast Search and Filter Performance

**Priority:** P0 · **Story Points:** 3

**As an** HR Manager,
**I want** search and filter operations to feel instant,
**So that** the application feels as fast as (or faster than) working with a local spreadsheet.

### Acceptance Criteria

- [ ] Search results return within 500ms for 10,000 employees
- [ ] Filter changes reflect in under 500ms
- [ ] Pagination navigation responds in under 300ms
- [ ] Analytics dashboard loads in under 2 seconds
- [ ] No visible UI jank or layout shift during data loading
- [ ] Loading indicators are shown for operations exceeding 200ms

---

## US-017: Responsive Desktop Layout

**Priority:** P2 · **Story Points:** 2

**As an** HR Manager,
**I want** the application to work well on my desktop and laptop screens,
**So that** I can use it comfortably on any workstation.

### Acceptance Criteria

- [ ] Layout renders correctly from 1024px to 1920px+ width
- [ ] Tables use horizontal scroll for narrow viewports rather than breaking layout
- [ ] Navigation remains accessible at all supported widths
- [ ] Charts resize appropriately without distortion
- [ ] No horizontal overflow or content clipping in standard usage

---

# Story Point Summary

| Epic | Stories | Total Points |
|------|---------|-------------|
| Epic 1: Employee Management | US-001 to US-008 | 30 |
| Epic 2: Compensation Analytics | US-009 to US-013 | 23 |
| Epic 3: Data Export | US-014 | 3 |
| Epic 4: Data Initialization | US-015 | 8 |
| Epic 5: Non-Functional | US-016, US-017 | 5 |
| **Total** | **17 stories** | **69 points** |

### By Priority

| Priority | Stories | Points |
|----------|---------|--------|
| **P0 — Must Have** | 12 | 55 |
| **P1 — Should Have** | 3 | 10 |
| **P2 — Nice to Have** | 2 | 4 |

---

# Out of Scope for Phase 1

The following capabilities are intentionally excluded from Phase 1 (see [REQUIREMENTS.md](./REQUIREMENTS.md) §4 for detailed reasoning):

| Excluded Feature | Key Reason |
|-----------------|------------|
| Authentication & Authorization | Would sit behind org SSO in production; adds complexity without demonstrating core value |
| Payroll Processing / Payments | Separate regulatory domain; tools like ADP/Deel handle this |
| Salary Revision History / Audit Trail | Requires temporal data model; strong V2 candidate |
| Multi-Currency Live Conversion | Static USD equivalent sufficient for compensation analysis |
| Excel/CSV Import | Robust import (column mapping, validation, conflict resolution) is a product in itself |
| Notifications / Email | No workflow in MVP requires notifications |
| Employee Self-Service Portal | Different user persona with different security model |
| AI/NLP Salary Chatbot | Structured dashboards answer HR questions more reliably than fragile NLP |

---

*Document Version: 2.0*
*Last Updated: June 9, 2026*
