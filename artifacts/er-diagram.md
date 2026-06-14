erDiagram

    TENANTS ||--o{ DEPARTMENTS : owns
    TENANTS ||--o{ EMPLOYEES : employs
    TENANTS ||--o{ PAYROLL_RUNS : generates

    DEPARTMENTS ||--o{ EMPLOYEES : contains

    EMPLOYEES ||--o{ SALARY_REVISIONS : has

    PAYROLL_RUNS ||--o{ PAYROLL_RECORDS : contains

    EMPLOYEES ||--o{ PAYROLL_RECORDS : receives

    TENANTS {
        uuid id PK
        string name
    }

    DEPARTMENTS {
        uuid id PK
        uuid tenant_id FK
        string name
    }

    EMPLOYEES {
        uuid id PK
        uuid tenant_id FK
        uuid department_id FK

        string employee_code
        string first_name
        string last_name
        string email

        string country

        int status

        date joining_date
        date termination_date

        datetime created_at
        datetime updated_at
    }

    SALARY_REVISIONS {
        uuid id PK
        uuid employee_id FK

        decimal annual_base_salary
        decimal monthly_allowance
        decimal monthly_deduction

        string currency

        int revision_number

        date effective_from
        date effective_to

        boolean is_current

        datetime created_at
    }

    PAYROLL_RUNS {
        uuid id PK
        uuid tenant_id FK

        int payroll_month
        int payroll_year

        int status

        datetime run_at
        string message
    }

    PAYROLL_RECORDS {
        uuid id PK

        uuid payroll_run_id FK
        uuid employee_id FK

        decimal gross_amount
        decimal deduction_amount
        decimal net_amount

        string currency

        datetime created_at
    }