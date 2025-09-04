import re
import hmac
import datetime as dt
from hashlib import sha256
from decimal import Decimal
from typing import Optional


def canonicalize_iban(s: str) -> str:
    # Uppercase + remove spaces; IBAN must be alnum by spec
    s = re.sub(r"\s+", "", s or "").upper()
    return s


def hmac_iban(secret: bytes, iban: str) -> str:
    """Return hex HMAC-SHA256 over canonical IBAN."""
    can = canonicalize_iban(iban)
    return hmac.new(secret, can.encode("utf-8"), sha256).hexdigest()


def last4(iban: str) -> str:
    can = canonicalize_iban(iban)
    return can[-4:] if len(can) >= 4 else can


def make_fingerprint(
    text: str,
    entity: str,
    account: str,
    amount: Decimal,
    date: dt.date,
    reference: Optional[str],
) -> str:
    raw = f"{text}|{entity}|{amount}|{account}|{date.isoformat()}|{reference}".encode()
    return sha256(raw).hexdigest()


# ----- Bank Service-level errors ---------------------------------------------------


class BankServiceError(Exception):
    """Base class for bank integration errors."""


class ExternalServiceError(BankServiceError):
    """Bank API returned an error or we failed to fetch data."""


# ----- Service-level errors ---------------------------------------------------


class ServiceError(Exception):
    """Base class for service errors."""


class NotFound(ServiceError):
    """Requested resource was not found."""


class Conflict(ServiceError):
    """Uniqueness or state conflict."""


class Ambiguous(ServiceError):
    """More than one matching resource found where one was expected."""


class BadRequest(ServiceError):
    """Invalid client request (e.g., payload-path mismatch)."""
