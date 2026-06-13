import random
import sys
import os
import uuid
from datetime import date, datetime, timedelta

# Ensure the root directory of the project is in the search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clients.database import SessionLocal
from models import Tenant, Department, Employee, SalaryRevision

random.seed(42)

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Sales", "Marketing",
    "Finance", "HR", "Legal", "Operations", "Customer Success",
    "Data Science", "Security", "IT", "Research", "Business Development",
]

LEVELS = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]

COUNTRIES = [
    ("United States", "USD"),
    ("United Kingdom", "GBP"),
    ("Germany", "EUR"),
    ("India", "INR"),
    ("Canada", "CAD"),
    ("Australia", "AUD"),
    ("France", "EUR"),
    ("Netherlands", "EUR"),
    ("Singapore", "SGD"),
    ("Brazil", "BRL"),
    ("Mexico", "MXN"),
    ("Poland", "PLN"),
    ("Spain", "EUR"),
    ("Sweden", "SEK"),
    ("Japan", "JPY"),
]

# Base USD salary bands by level
LEVEL_SALARY_USD = {
    "L1": (45_000,  64_000),
    "L2": (66_000,  89_000),
    "L3": (91_000, 119_000),
    "L4": (121_000, 159_000),
    "L5": (161_000, 209_000),
    "L6": (211_000, 269_000),
    "L7": (271_000, 400_000),
}

# Cost-of-living multipliers (relative to USD)
COL_MULTIPLIER = {
    "USD": 1.00, "GBP": 0.85, "EUR": 0.80,
    "INR": 0.30, "CAD": 0.90, "AUD": 0.88,
    "SGD": 0.90, "BRL": 0.35, "MXN": 0.35,
    "PLN": 0.55, "SEK": 0.85, "JPY": 0.75,
}

# Country distribution weights (bigger offices in US/India/UK)
COUNTRY_WEIGHTS = [30, 12, 8, 18, 6, 5, 5, 4, 3, 2, 2, 1, 1, 1, 2]

def random_date(start_year=2010, end_year=2025):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def generate_salary(level: str, currency: str, dept: str) -> tuple[float, float, float]:
    lo, hi = LEVEL_SALARY_USD[level]
    base_usd = random.uniform(lo, hi)
    col = COL_MULTIPLIER.get(currency, 0.80)
    base = round(base_usd * col, -2)  # round to nearest 100

    # Engineering / Data Science premiums
    if dept in ("Engineering", "Data Science", "Security"):
        base *= random.uniform(1.05, 1.20)
        base = round(base, -2)

    monthly_base = base / 12
    # Scale monthly allowance and deduction proportionally to prevent overlap
    allowance = round(monthly_base * random.uniform(0.05, 0.15), 2)
    deduction = round(monthly_base * random.uniform(0.02, 0.08), 2)

    return base, allowance, deduction

def generate_salary_history(emp_id: uuid.UUID, base: float, allowance: float, deduction: float, currency: str, joining_date: date) -> list[SalaryRevision]:
    revisions = []
    current_year = 2026
    years_employed = current_year - joining_date.year
    
    # Determine the number of revisions based on tenure
    if years_employed >= 6:
        num_revisions = 3
    elif years_employed >= 3:
        num_revisions = 2
    else:
        num_revisions = 1
        
    if num_revisions == 1:
        # Single current revision
        revisions.append(SalaryRevision(
            id=uuid.uuid4(),
            employee_id=emp_id,
            annual_base_salary=base,
            monthly_allowance=allowance,
            monthly_deduction=deduction,
            currency=currency,
            revision_number=1,
            effective_from=joining_date,
            effective_to=None,
            is_current=True
        ))
    elif num_revisions == 2:
        # Revision 1 (historical, 15% lower)
        eff_to = joining_date + timedelta(days=730)
        revisions.append(SalaryRevision(
            id=uuid.uuid4(),
            employee_id=emp_id,
            annual_base_salary=round(base * 0.85, 2),
            monthly_allowance=round(allowance * 0.85, 2),
            monthly_deduction=round(deduction * 0.85, 2),
            currency=currency,
            revision_number=1,
            effective_from=joining_date,
            effective_to=eff_to,
            is_current=False
        ))
        # Revision 2 (current)
        revisions.append(SalaryRevision(
            id=uuid.uuid4(),
            employee_id=emp_id,
            annual_base_salary=base,
            monthly_allowance=allowance,
            monthly_deduction=deduction,
            currency=currency,
            revision_number=2,
            effective_from=eff_to,
            effective_to=None,
            is_current=True
        ))
    else:
        # Revision 1 (historical, 30% lower)
        eff_to_1 = joining_date + timedelta(days=730)
        revisions.append(SalaryRevision(
            id=uuid.uuid4(),
            employee_id=emp_id,
            annual_base_salary=round(base * 0.70, 2),
            monthly_allowance=round(allowance * 0.70, 2),
            monthly_deduction=round(deduction * 0.70, 2),
            currency=currency,
            revision_number=1,
            effective_from=joining_date,
            effective_to=eff_to_1,
            is_current=False
        ))
        # Revision 2 (historical, 15% lower)
        eff_to_2 = eff_to_1 + timedelta(days=730)
        revisions.append(SalaryRevision(
            id=uuid.uuid4(),
            employee_id=emp_id,
            annual_base_salary=round(base * 0.85, 2),
            monthly_allowance=round(allowance * 0.85, 2),
            monthly_deduction=round(deduction * 0.85, 2),
            currency=currency,
            revision_number=2,
            effective_from=eff_to_1,
            effective_to=eff_to_2,
            is_current=False
        ))
        # Revision 3 (current)
        revisions.append(SalaryRevision(
            id=uuid.uuid4(),
            employee_id=emp_id,
            annual_base_salary=base,
            monthly_allowance=allowance,
            monthly_deduction=deduction,
            currency=currency,
            revision_number=3,
            effective_from=eff_to_2,
            effective_to=None,
            is_current=True
        ))
        
    return revisions

def seed_employees():
    db = SessionLocal()
    try:
        # Resolve Tenant ACME
        tenant = db.query(Tenant).filter_by(name="ACME").first()
        if not tenant:
            print("Error: Tenant 'ACME' not found! Please run company seeder first.")
            return
            
        tenant_id = tenant.id

        # Resolve Departments Mapping
        depts = db.query(Department).filter_by(tenant_id=tenant_id).all()
        dept_map = {d.name: d.id for d in depts}
        if not dept_map:
            print("Error: No departments found! Please run department seeder first.")
            return

        existing = db.query(Employee).filter_by(tenant_id=tenant_id).count()
        if existing >= 10_000:
            print(f"Already have {existing} employees for tenant ACME — skipping seed.")
            return

        print("Seeding 10,000 employees with SCD 2 salary history …")
        employees = []
        salary_revisions = []

        for i in range(1, 10_001):
            fname = random.choice(FIRST_NAMES := ["Liam","Noah","Oliver","James","Elijah","William","Lucas","Mason","Ethan","Aiden","Emma","Olivia","Ava","Isabella","Sophia","Mia","Charlotte","Amelia","Harper","Evelyn","Riya","Aarav","Priya","Rohan","Ananya","Arjun","Neha","Kavya","Aryan","Ishaan","Leon","Mia","Felix","Hannah","Paul","Lena","Jonas","Sarah","Max","Laura","Mohammed","Fatima","Omar","Aisha","Yusuf","Zara","Hassan","Layla","Ahmad","Nour","Wei","Jing","Fang","Chen","Li","Hui","Yang","Ming","Xiao","Ting","Carlos","Maria","Jose","Ana","Juan","Sofia","Diego","Valentina","Luis","Camila","Luca","Giulia","Marco","Chiara","Matteo","Sara","Alessandro","Francesca","Lorenzo","Elena"])
            lname = random.choice(LAST_NAMES := ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Moore","Taylor","Anderson","Thomas","Jackson","White","Harris","Martin","Thompson","Young","King","Patel","Sharma","Singh","Kumar","Joshi","Mehta","Shah","Gupta","Iyer","Reddy","Müller","Schmidt","Schneider","Fischer","Weber","Meyer","Wagner","Becker","Schulz","Hoffmann","Chen","Wang","Li","Zhang","Liu","Huang","Zhao","Wu","Zhou","Sun","Silva","Santos","Oliveira","Costa","Souza","Ferreira","Alves","Pereira","Lima","Carvalho","Kowalski","Nowak","Wiśniewski","Wójcik","Kowalczyk","Kamińska","Zielińska","Szymańska","Woźniak","Dąbrowski","Tanaka","Suzuki","Watanabe","Ito","Yamamoto","Nakamura","Kobayashi","Kato","Saito","Yamada"])
            
            dept_name = random.choice(DEPARTMENTS)
            dept_id = dept_map.get(dept_name)
            
            level = random.choices(LEVELS, weights=[20, 25, 22, 16, 10, 5, 2])[0]
            country, currency = random.choices(COUNTRIES, weights=COUNTRY_WEIGHTS)[0]
            base, allowance, deduction = generate_salary(level, currency, dept_name)
            joining_date = random_date()

            domain_map = {
                "United States": "acme.com", "United Kingdom": "acme.co.uk",
                "Germany": "acme.de", "India": "acme.in",
                "Canada": "acme.ca", "Australia": "acme.com.au",
            }
            domain = domain_map.get(country, "acme.io")
            email = f"{fname.lower()}.{lname.lower()}{i}@{domain}"
            status = random.choices([1, 0], weights=[95, 5])[0] # 1 = Active, 0 = Inactive

            emp_id = uuid.uuid4()
            emp = Employee(
                id=emp_id,
                tenant_id=tenant_id,
                department_id=dept_id,
                employee_code=f"ACME-{i:05d}",
                first_name=fname,
                last_name=lname,
                email=email,
                country=country,
                status=status,
                joining_date=joining_date,
            )
            employees.append(emp)

            # Generate SCD 2 salary history revisions
            revisions = generate_salary_history(emp_id, base, allowance, deduction, currency, joining_date)
            salary_revisions.extend(revisions)

            if i % 1000 == 0:
                db.bulk_save_objects(employees)
                db.bulk_save_objects(salary_revisions)
                db.commit()
                employees = []
                salary_revisions = []
                print(f"  {i}/10000 done")

        if employees:
            db.bulk_save_objects(employees)
            db.bulk_save_objects(salary_revisions)
            db.commit()

        print("Seeding complete.")
    finally:
        db.close()
