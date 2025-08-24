import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Iterator
from .models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


# SQLite URL (file)
load_dotenv()
DB_PATH = Path(os.getenv("DB_PATH")).resolve()
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# Engine (check_same_thread=False for SQLite in FastAPI sync handlers)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Iterator[Session]:
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except:
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
