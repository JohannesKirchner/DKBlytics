"""
Shared pytest fixtures for the FastAPI app in `src/`.

Key behaviors:
- Uses a **temporary file-based SQLite DB** per test session (via DB_PATH env var).
- Reloads `src.database` after setting DB_PATH so the engine points to the temp DB.
- Calls `initialize_database()` so tables exist before tests run.
- Exposes a `client` fixture using FastAPI's `TestClient`.
- Provides small data factories for convenience.
"""

import os
import sys
import json
import tempfile
import importlib
from pathlib import Path
import pytest

# Ensure the project root (containing the `src` package) is importable
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def tmp_db_file():
    # file-based SQLite is safest with multiple connections/threads
    fd, path = tempfile.mkstemp(suffix=".sqlite3")
    os.close(fd)
    try:
        yield path
    finally:
        os.remove(path)


@pytest.fixture(scope="session")
def client(tmp_db_file):
    # Set DB_PATH before importing/reloading the DB module
    os.environ["DB_PATH"] = tmp_db_file

    # Import and reload database to rebind engine/session to the test DB
    import src.database as dbmod

    importlib.reload(dbmod)

    # Make sure tables exist
    dbmod.initialize_database()

    # Now import the FastAPI app
    from fastapi.testclient import TestClient
    from src.main import app

    # Start the app with lifespan events
    with TestClient(app) as c:
        yield c
