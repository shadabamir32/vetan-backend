from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid

from clients.database import get_db
from routes import employees

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

# Tenant verification middleware
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    # Bypass paths that do not require tenant scoping (like health checks or documentation docs)
    exempt_prefixes = [
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/redoc"
    ]
    is_exempt = any(request.url.path.startswith(prefix) for prefix in exempt_prefixes)
    
    if is_exempt or not request.url.path.startswith("/api"):
        return await call_next(request)

    x_tenant_id = request.headers.get("x-tenant-id")
    if not x_tenant_id:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized: X-Tenant-ID header is missing."}
        )

    try:
        tenant_uuid = uuid.UUID(x_tenant_id)
    except ValueError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Unauthorized: X-Tenant-ID header must be a valid UUID."}
        )

    # Store resolved tenant UUID in request state for downstream handlers
    request.state.tenant_id = tenant_uuid

    response = await call_next(request)
    return response

# Register routers under version v1
app.include_router(employees.router, prefix="/api/v1")

@app.get("/api/v1/health", tags=["Health"])
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
