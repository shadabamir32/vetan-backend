import os
from dotenv import load_dotenv

# Load the environment variables from the .env file
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASES = {
    "default": os.getenv("DB_CONNECTION", "sqlite"),
    "connections": {
        "sqlite": {
            "driver": "sqlite",
            "database": os.getenv("DB_DATABASE", os.path.join(BASE_DIR, "salaryapp.db")),
        },
        "mysql": {
            "driver": "mysql",
            "host": os.getenv("DB_HOST", "127.0.0.1"),
            "port": os.getenv("DB_PORT", "3306"),
            "database": os.getenv("DB_DATABASE", "vetan_db"),
            "username": os.getenv("DB_USERNAME", "root"),
            "password": os.getenv("DB_PASSWORD", ""),
            "charset": os.getenv("DB_CHARSET", "utf8mb4"),
        }
    }
}

def get_connection_url(connection_name: str) -> str:
    """
    Generates a SQLAlchemy connection URL based on the connection configuration.
    """
    config = DATABASES["connections"].get(connection_name)
    if not config:
        raise ValueError(f"Database connection '{connection_name}' is not configured.")

    driver = config.get("driver")
    if driver == "sqlite":
        db_path = config.get("database", "salaryapp.db")
        # Ensure SQLite path is formatted correctly for SQLAlchemy (3 slashes for relative/absolute in general)
        return f"sqlite:///{db_path}"
    elif driver == "mysql":
        username = config.get("username", "root")
        password = config.get("password", "")
        host = config.get("host", "127.0.0.1")
        port = config.get("port", "3306")
        database = config.get("database", "vetan_db")
        charset = config.get("charset", "utf8mb4")
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset={charset}"
    else:
        raise ValueError(f"Unsupported database driver '{driver}' for connection '{connection_name}'.")
