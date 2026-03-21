# src/settings.py
import os
import base64
import binascii
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()  # loads from .env if present

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


def _load_bytes_from_env(var: str) -> bytes:
    val = os.getenv(var, "")
    if not val:
        raise RuntimeError(f"{var} must be set (use a random 32-byte key).")
    # Try hex
    try:
        return bytes.fromhex(val)
    except ValueError:
        pass
    # Try base64
    try:
        return base64.b64decode(val, validate=True)
    except binascii.Error:
        pass
    # Fallback: treat as raw utf-8 (allowed for dev, not recommended for prod)
    return val.encode("utf-8")


# 32+ bytes recommended
IBAN_HMAC_KEY: bytes = _load_bytes_from_env("IBAN_HMAC_KEY")


def cors_origins_from_env() -> list[str]:
    raw = os.getenv("FRONTEND_ORIGINS", "")
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]