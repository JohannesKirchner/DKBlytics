import datetime as dt
from hashlib import sha1
from decimal import Decimal
from typing import Optional


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
