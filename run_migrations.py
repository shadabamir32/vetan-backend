import argparse
import sys
from migrations.migrations import run_migrations
from models import Base
from clients.database import engine

def main() -> None:
    parser = argparse.ArgumentParser(description="Vetan Database Migration & Seeding CLI Tool")
    parser.add_argument(
        "--recreate", "-r",
        action="store_true",
        help="Recreate the database from scratch (drops all tables first, like migrate:fresh)"
    )
    parser.add_argument(
        "--seed", "-s",
        action="store_true",
        help="Run database seeders after migrating"
    )
    
    args = parser.parse_args()
    
    if args.recreate:
        print("Warning: Recreating database. Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("All existing tables dropped.")
        
    print("Running database migrations...")
    run_migrations()
    print("Database migrations completed.")
    
    if args.seed:
        from seed_run import seeds_db
        seeds_db()

if __name__ == "__main__":
    main()