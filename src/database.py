import os
from pathlib import Path
from .models import Base
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Resolve DB path with a sensible default
_db_env = os.getenv("DB_PATH")
if not _db_env or not _db_env.strip():
    default_dir = Path("./.data")
    default_dir.mkdir(parents=True, exist_ok=True)
    DB_PATH = (default_dir / "app.db").resolve()
    print(f"[database] DB_PATH not set; using default SQLite DB at {DB_PATH}")
else:
    DB_PATH = Path(_db_env).expanduser().resolve()

SQLALCHEMY_DATABASE_URL = f"sqlite:///{Path(DB_PATH).resolve()}"

# Engine (SQLite needs check_same_thread=False in threaded servers)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,  # avoid stale pooled connections
)


# Enforce SQLite foreign keys
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        # Optional: log this if you have a logger configured
        pass


# Session factory: conservative, API-friendly defaults
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # lets you serialize ORM objects after commit
)


# Typical FastAPI dependency (keep if you already have it elsewhere)
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as create_all_err:
        raise RuntimeError(f"fallback create_all error: {create_all_err!r}")
