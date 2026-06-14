import sys
import os

# Ensure the root directory of the project is in the search path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from seeds.company_seeder_v1 import seed_companies
from seeds.department_seeder_v1 import seed_departments
from seeds.employee_seeder_v1 import seed_employees

def seeds_db():
    print("Starting database seeding process...")
    
    print("\n--- Seeding Tenants ---")
    seed_companies()
    
    print("\n--- Seeding Departments ---")
    seed_departments()
    
    print("\n--- Seeding Employees & Salary Revisions ---")
    seed_employees()
    
    print("\nDatabase seeding completed successfully.")


if __name__ == "__main__":
    seeds_db()
