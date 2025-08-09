from datetime import date
from hashlib import sha1
from decimal import Decimal
from typing import Optional


def make_fingerprint(
    text: str,
    entity: str,
    account: str,
    amount: Decimal,
    date_: date,
    reference: Optional[str],
) -> str:
    raw = f"{text}|{entity}|{amount}|{account}|{date_.isoformat()}|{str(reference)}".encode()
    return sha1(raw).hexdigest()
