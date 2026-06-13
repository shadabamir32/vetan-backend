import uuid
from clients.database import engine, SessionLocal
from models import Base, Tenant

# Ensure tables are created in the database
Base.metadata.create_all(bind=engine)

def seed_companies():
    db = SessionLocal()
    try:
        # Default tenant data
        tenant_id = uuid.UUID("7817f7d1-e630-4e31-97b7-7e618f0a2dbd")
        tenant_name = "ACME"

        # Check if tenant already exists
        existing = db.query(Tenant).filter_by(id=tenant_id).first()
        if existing:
            print(f"Tenant '{tenant_name}' ({tenant_id}) already exists. Skipping onboarding.")
            return

        print(f"Onboarding tenant: '{tenant_name}' ({tenant_id})")
        tenant = Tenant(
            id=tenant_id,
            name=tenant_name
        )
        db.add(tenant)
        db.commit()
        print("Tenant onboarded successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_companies()
