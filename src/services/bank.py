from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy.orm import Session

from dkb_robo import DKBRobo  # external lib

from ..schemas import AccountCreate, TransactionCreate
from ..services.accounts import (
    create_account_db,
    update_account_db,
    get_account_by_iban_hmac_db,
)
from ..services.transactions import create_transaction_db
from ..settings import load_credentials, IBAN_HMAC_KEY
from ..utils import hmac_iban, ExternalServiceError, Conflict, NotFound


# ----- Helpers ----------------------------------------------------------------


@dataclass(frozen=True)
class BankAccount:
    name: str
    amount: Optional[Any]  # Decimal-like or numeric
    iban: str
    holder_name: str


@dataclass(frozen=True)
class BankTransaction:
    text: str
    peer: str
    amount: Any
    date: Any
    customerreference: Optional[str]


def _parse_date(value: Any) -> dt.date:
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


# ----- Fetch from bank --------------------------------------------------------


def fetch_bank_data() -> Tuple[List[BankAccount], List[List[BankTransaction]]]:
    """
    Fetch accounts and their transactions from DKB.

    Returns:
        (accounts, account_transactions)
        where accounts[i] corresponds to account_transactions[i]
    """
    user, pwd, mfa = load_credentials()

    try:
        with DKBRobo(
            dkb_user=user,
            dkb_password=pwd,
            chip_tan=False,
            mfa_device=mfa,
            debug=False,
            unfiltered=False,
        ) as dkb:
            # Collect accounts
            accounts_raw = list(dkb.account_dic.values())

            # Collect transactions per account (from Jan 1, 2023 until today)
            date_from = "01.01.2023"
            date_to = dt.datetime.now().strftime("%d.%m.%Y")
            txs_per_account_raw = []
            for acc in accounts_raw:
                txs = dkb.get_transactions(
                    acc["transactions"],
                    acc["type"],
                    date_from,
                    date_to,
                )
                txs_per_account_raw.append(txs)

    except Exception as exc:
        raise ExternalServiceError(f"Failed to fetch data from DKB: {exc!r}") from exc

    # Normalize to our dataclasses
    accounts: List[BankAccount] = [
        BankAccount(
            name=a.get("name", "").strip(),
            amount=a.get("amount"),
            iban=a.get("iban"),
            holder_name=a.get("holdername") or a.get("holderName"),
        )
        for a in accounts_raw
    ]

    account_transactions: List[List[BankTransaction]] = []
    for tx_list in txs_per_account_raw:
        norm_list: List[BankTransaction] = []
        for t in tx_list:
            norm_list.append(
                BankTransaction(
                    text=t.get("text", "") or "",
                    peer=t.get("peer", "") or "",
                    amount=t.get("amount"),
                    date=t.get("date"),
                    customerreference=t.get("customerreference"),
                )
            )
        account_transactions.append(norm_list)

    return accounts, account_transactions


# ----- Import into our DB -----------------------------------------------------


def get_new_transactions(db: Session) -> Dict[str, int]:
    """
    Fetch new data from the bank and insert into our DB.

    - Creates accounts if missing; otherwise updates the balance to the bank-reported amount.
    - Inserts transactions using the transaction service, passing a common batch_hash.
    - Duplicate policy is enforced by the transaction service:
        * Allowed: duplicates when SAME (fingerprint, batch_hash)
        * Rejected: if a matching fingerprint already exists with a DIFFERENT batch_hash
    Returns:
        dict mapping account_name -> number of transactions inserted for that account in this run.
    """
    # One batch hash for this whole import run (64-char hex; matches DB size)
    batch_hash = sha256(str(dt.datetime.now().isoformat()).encode("utf-8")).hexdigest()

    try:
        accounts, account_transactions = fetch_bank_data()
    except ExternalServiceError:
        # Bubble up unchanged for the router to map to 502
        raise

    inserted_counts: Dict[str, int] = defaultdict(int)
    for account, transactions in zip(accounts, account_transactions):
        if not account.iban:
            # Skip nameless accounts defensively
            continue

        # Create or update account
        if account.amount is None:
            # If balance not present, we still ensure the account exists with balance=0
            balance_value = 0
        else:
            balance_value = account.amount

        iban_h = hmac_iban(IBAN_HMAC_KEY, account.iban)
        try:
            # Already exists → update balance only
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
            # Account Not Found -> create new
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
                    batch_hash=batch_hash,  # pass batch to satisfy duplicate policy
                )
                create_transaction_db(db, payload)
                inserted_counts[account.name] += 1
            except Conflict:
                # Cross-batch duplicate → skip silently for this batch
                continue
            except ExternalServiceError:
                # Parse error on date or similar normalization issue
                continue

    return dict(inserted_counts)
