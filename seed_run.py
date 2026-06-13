import sys
import os

# Ensure the root directory of the project is in the search path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from seeds.company_seeder import seed_companies

if __name__ == "__main__":
    print("Starting database seeding process...")
    seed_companies()
