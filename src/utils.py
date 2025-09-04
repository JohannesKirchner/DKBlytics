import re
import hmac
import datetime as dt
from hashlib import sha1, sha256
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
    return sha1(raw).hexdigest()
