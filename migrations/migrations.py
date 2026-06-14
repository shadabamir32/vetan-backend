from sqlalchemy import inspect, text
from clients.database import engine, SessionLocal
from models import Base

def run_migrations() -> None:
    """
    Automated schema migration:
    1. Creates any missing tables.
    2. Identifies and adds any missing columns on existing tables by comparing
       database metadata against Python SQLAlchemy models.
    """
    # Create any tables that don't exist yet
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    db = SessionLocal()
    
    try:
        # Scan all tables defined in models.py
        for table_name, table_obj in Base.metadata.tables.items():
            # Get columns currently in the database
            existing_columns = inspector.get_columns(table_name)
            existing_col_names = {col["name"] for col in existing_columns}
            
            # Compare with columns declared in the Python model
            for col_name, column_obj in table_obj.columns.items():
                if col_name not in existing_col_names:
                    # Generate type name (e.g. VARCHAR, INTEGER, NUMERIC, etc.)
                    col_type = str(column_obj.type)
                    
                    print(f"Migration: Adding column '{col_name}' ({col_type}) to table '{table_name}'...")
                    
                    # Generate and execute ALTER TABLE query (valid for both SQLite and MySQL)
                    alter_query = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};"
                    db.execute(text(alter_query))
                    db.commit()
                    print(f"Migration: Column '{col_name}' added successfully.")
                    
    except Exception as e:
        db.rollback()
        print(f"Migration error: {str(e)}")
    finally:
        db.close()
