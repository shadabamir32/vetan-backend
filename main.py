from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from clients.database import get_db
from routes import employees, salaries, payroll

app = FastAPI(
    title="Vetan Salary & Payroll Backend",
    description="Salary and Payroll management API backend.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under version v1
app.include_router(employees.router, prefix="/api/v1")
app.include_router(salaries.router, prefix="/api/v1")
app.include_router(payroll.router, prefix="/api/v1")

@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """
    Service and database health check endpoint.
    """
    try:
        # Run a simple query to verify database connectivity
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "service": "vetan-backend"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {str(e)}"
        )

