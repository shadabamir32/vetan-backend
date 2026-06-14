# System Architecture Diagram

Below is the high-level architecture diagram showing the relationship between the user, the frontend application, the backend API server, and the database storage layer.

---

```mermaid
graph LR
    Actor["HR Manager"] -- "Interacts with UI" --> Frontend["React Frontend (SPA)"]
    Frontend -- "HTTP REST Requests" --> Backend["FastAPI Backend Server"]
    Backend -- "SQL Queries (SQLAlchemy ORM)" --> Database[("SQLite Database (salaryapp.db)")]

    %% Styling
    style Actor fill:#181c27,stroke:#2a3050,stroke-width:2px,color:#f0f2f8;
    style Frontend fill:#1e2333,stroke:#4f8ef7,stroke-width:2px,color:#f0f2f8;
    style Backend fill:#1e2333,stroke:#3d4a72,stroke-width:2px,color:#f0f2f8;
    style Database fill:#0f1117,stroke:#2a3050,stroke-width:2px,color:#f0f2f8;
```
