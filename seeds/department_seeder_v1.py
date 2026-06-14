import uuid
from clients.database import SessionLocal
from models import Department, Tenant

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Sales", "Marketing",
    "Finance", "HR", "Legal", "Operations", "Customer Success",
    "Data Science", "Security", "IT", "Research", "Business Development",
]

def seed_departments():
    db = SessionLocal()
    try:
        # Retrieve tenant by name
        tenant = db.query(Tenant).filter_by(name="ACME").first()
        if not tenant:
            print("Error: Tenant 'ACME' not found! Please run company seeder first.")
            return

        tenant_id = tenant.id
        print(f"Seeding {len(DEPARTMENTS)} departments for tenant: {tenant.name} ...")
        
        added_count = 0
        for name in DEPARTMENTS:
            # Generate deterministic UUID
            dept_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"acme.com/departments/{name}")
            
            # Check if department already exists
            existing = db.query(Department).filter_by(id=dept_id).first()
            if not existing:
                dept = Department(
                    id=dept_id,
                    tenant_id=tenant_id,
                    name=name
                )
                db.add(dept)
                added_count += 1

        if added_count > 0:
            db.commit()
            print(f"Successfully seeded {added_count} new departments.")
        else:
            print("All departments already exist. Skipping.")
            
    finally:
        db.close()

if __name__ == "__main__":
    seed_departments()
