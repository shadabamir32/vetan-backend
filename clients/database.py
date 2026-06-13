from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.db import DATABASES, get_connection_url


class DatabaseConnection:
    """
    Represents a specific database connection instance.
    Provides utility methods to interact with the engine and session factories.
    Supports Python context manager protocol to handle transaction scoping automatically.
    """
    def __init__(self, engine, session_factory):
        self.engine = engine
        self._session_factory = session_factory
        self._session = None

    def get_session(self):
        """
        Creates and returns a new SQLAlchemy session instance.
        The caller is responsible for committing/rolling back and closing the session.
        """
        return self._session_factory()

    def __enter__(self):
        """
        Enters a database session context.
        """
        self._session = self.get_session()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exits the database session context.
        Automatically commits changes if no exception occurred, or rolls back if an exception was raised.
        Closes the session at the end.
        """
        if self._session:
            if exc_type is not None:
                self._session.rollback()
            else:
                try:
                    self._session.commit()
                except Exception:
                    self._session.rollback()
                    raise
            self._session.close()
            self._session = None


class DatabaseManager:
    """
    Manager to dynamically resolve, cache, and manage multiple database connections (drivers).
    Inspired by Laravel's database manager.
    """
    def __init__(self):
        self._engines = {}
        self._session_factories = {}

    def driver(self, name: str = None) -> DatabaseConnection:
        """
        Gets a DatabaseConnection instance for the specified driver name.
        If no name is specified, the default connection configured in DATABASES is returned.
        """
        if name is None:
            name = DATABASES["default"]

        if name not in self._engines:
            if name not in DATABASES["connections"]:
                raise ValueError(f"Database connection '{name}' is not configured.")

            url = get_connection_url(name)
            config = DATABASES["connections"][name]
            driver = config.get("driver")

            engine_args = {}
            if driver == "sqlite":
                engine_args["connect_args"] = {"check_same_thread": False}
                db_path = config.get("database", "salaryapp.db")
                if db_path == ":memory:":
                    from sqlalchemy.pool import StaticPool
                    engine_args["poolclass"] = StaticPool
                else:
                    engine_args["pool_size"] = 20
                    engine_args["max_overflow"] = 40
            elif driver == "mysql":
                engine_args["pool_size"] = 20
                engine_args["max_overflow"] = 40
                engine_args["pool_recycle"] = 3600

            self._engines[name] = create_engine(url, **engine_args)
            self._session_factories[name] = sessionmaker(
                autocommit=False, autoflush=False, bind=self._engines[name]
            )

        return DatabaseConnection(self._engines[name], self._session_factories[name])

    @property
    def engine(self):
        """
        Returns the SQLAlchemy engine for the default connection.
        Useful for metadata binding (e.g. Base.metadata.create_all).
        """
        return self.driver().engine

    @property
    def session_local(self):
        """
        Returns the sessionmaker callable for the default connection.
        Allows legacy code invoking `SessionLocal()` to function.
        """
        return self.driver()._session_factory


# Initialize the database manager
db = DatabaseManager()

# Export engine and SessionLocal directly for backwards compatibility with legacy seeders and imports
engine = db.engine
SessionLocal = db.session_local


def get_db():
    """
    FastAPI dependency that yields a database session from the default connection.
    Autocloses when done.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

