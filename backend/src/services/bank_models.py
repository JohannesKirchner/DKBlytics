"""Bank data models - shared dataclasses for banking integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any


@dataclass(frozen=True)
class BankAccount:
    """Minimal representation of a bank account."""
    
    name: str
    amount: Optional[Any]  # Decimal-like or numeric
    iban: str
    holder_name: str


@dataclass(frozen=True)  
class BankTransaction:
    """Minimal representation of a bank transaction."""
    
    text: str
    peer: str
    amount: Any
    date: Any
    customerreference: Optional[str]