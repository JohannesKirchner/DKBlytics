"""Bank integration service - CSV import functionality."""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from hashlib import sha256
from typing import Dict, List, BinaryIO

from sqlalchemy.orm import Session

from ..schemas import AccountCreate, TransactionCreate
from ..services.accounts import (
    create_account_db,
    update_account_db,
    get_account_by_iban_hmac_db,
)
from ..services.transactions import create_transaction_db
from ..settings import IBAN_HMAC_KEY
from ..utils import hmac_iban, ExternalServiceError, Conflict, NotFound
from .bank_models import BankAccount, BankTransaction
from .csv_parsers import parse_csv_file


def _parse_date(value) -> dt.date:
    """Accept date/datetime/str and return a date. Be forgiving about formats."""
    if isinstance(value, dt.date) and not isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, str):
        # Try common bank formats first: DD.MM.YYYY, then ISO
        for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
            try:
                return dt.datetime.strptime(value, fmt).date()
            except ValueError:
                pass
    # As a last resort, let it blow up clearly
    raise ExternalServiceError(f"Unsupported date format from bank: {value!r}")


# ----- CSV Import Functions ---------------------------------------------------


def import_bank_payload(
    db: Session,
    accounts: List[BankAccount],
    account_transactions: List[List[BankTransaction]]
) -> Dict[str, int]:
    """Import bank data (accounts and transactions) into the database.
    
    This is the common import pipeline used by both live API and CSV import.
    Handles account creation/update and transaction insertion with duplicate detection.
    
    Args:
        db: Database session
        accounts: List of bank accounts
        account_transactions: List of transaction lists, one per account
        
    Returns:
        Dict mapping account names to number of inserted transactions
    """
    if len(accounts) != len(account_transactions):
        raise ExternalServiceError(
            "Mismatched number of accounts and transaction lists"
        )

    # One batch hash for this whole import run (64-char hex; matches DB size)
    batch_hash = sha256(str(dt.datetime.now().isoformat()).encode("utf-8")).hexdigest()

    inserted_counts: Dict[str, int] = defaultdict(int)
    for account, transactions in zip(accounts, account_transactions):
        if not account.iban:
            # Skip accounts without IBAN
            continue

        # Create or update account
        balance_value = account.amount if account.amount is not None else 0

        iban_h = hmac_iban(IBAN_HMAC_KEY, account.iban)
        try:
            # Account exists → update balance
            existing_account = get_account_by_iban_hmac_db(db, iban_hmac=iban_h)
            new_or_updated_account = update_account_db(
                db,
                public_id=existing_account.public_id,
                payload=AccountCreate(
                    name=account.name,
                    holder_name=account.holder_name,
                    iban_plain=account.iban,
                    balance=balance_value,
                ),
            )
        except NotFound:
            # Account doesn't exist → create new
            new_or_updated_account = create_account_db(
                db,
                AccountCreate(
                    name=account.name,
                    holder_name=account.holder_name,
                    iban_plain=account.iban,
                    balance=balance_value,
                ),
            )

        # Insert transactions
        for t in transactions:
            try:
                payload = TransactionCreate(
                    text=t.text,
                    entity=t.peer,
                    account_id=new_or_updated_account.public_id,
                    amount=t.amount,
                    date=_parse_date(t.date),
                    reference=t.customerreference,
                    batch_hash=batch_hash,
                )
                create_transaction_db(db, payload)
                inserted_counts[account.name] += 1
            except Conflict:
                # Cross-batch duplicate → skip silently
                continue
            except ExternalServiceError:
                # Parse error on date or similar normalization issue
                continue

    return dict(inserted_counts)




def import_csv_data(
    db: Session,
    file_obj: BinaryIO, 
    parser_type: str,
    holder_name: str
) -> Dict[str, int]:
    """Import transactions from a CSV file using the specified parser.
    
    This function integrates CSV parsing with the existing duplicate detection
    and import pipeline, reusing the same logic as get_new_transactions().
    
    Args:
        db: Database session
        file_obj: File object containing CSV data
        parser_type: Parser identifier (e.g., 'dkb')
        holder_name: Account holder name
        
    Returns:
        Dict mapping account names to number of inserted transactions
        
    Raises:
        ExternalServiceError: If parsing fails or CSV format is invalid
    """
    try:
        # Parse CSV file into BankAccount and BankTransaction objects
        parsed_data = parse_csv_file(file_obj, parser_type, holder_name)
        
        # Use existing import pipeline - this handles all duplicate detection,
        # account creation/update, and transaction insertion
        return import_bank_payload(
            db=db,
            accounts=parsed_data.accounts,
            account_transactions=parsed_data.transactions_per_account
        )
        
    except ValueError as e:
        # Parser errors become ExternalServiceError for consistent error handling
        raise ExternalServiceError(f"CSV parsing error: {str(e)}") from e
