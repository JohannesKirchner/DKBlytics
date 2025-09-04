from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Account as AccountORM
from ..schemas import Account, AccountCreate
from ..utils import hmac_iban, last4, canonicalize_iban
from ..settings import IBAN_HMAC_KEY
from ..utils import Conflict, NotFound


def create_account_db(db: Session, payload: AccountCreate) -> Account:
    """
    Create a new account with a unique IBAN.

    Raises Conflict if an account with the same IBAN already exists. The plain IBAN
    is not stored in the database but encrypted.
    """
    iban_plain = canonicalize_iban(payload.iban_plain)
    iban_h = hmac_iban(IBAN_HMAC_KEY, iban_plain)
    obj = AccountORM(
        name=payload.name,
        holder_name=payload.holder_name,
        iban_hmac=iban_h,
        iban_last4=last4(iban_plain),
        balance=payload.balance,
    )
    try:
        db.add(obj)
        db.flush()
    except IntegrityError as ie:
        db.rollback()
        raise Conflict("Account with this IBAN already exists.") from ie
    return Account.model_validate(obj)


def update_account_db(db: Session, public_id: str, payload: AccountCreate) -> Account:
    """
    Update an existing account's balance.

    - Raises NotFound if the account does not exist.
    - Raises Conflict if the IBAN is already in use by another account.
    """
    obj = db.scalar(select(AccountORM).where(AccountORM.public_id == public_id))
    if not obj:
        raise NotFound("Account not found.")
    # Recompute HMAC if IBAN changed (optional)
    iban_h = hmac_iban(IBAN_HMAC_KEY, payload.iban_plain)
    obj.name = payload.name
    obj.holder_name = payload.holder_name
    obj.iban_hmac = iban_h
    obj.iban_last4 = last4(payload.iban_plain)
    obj.balance = payload.balance
    try:
        db.flush()
    except IntegrityError as ie:
        db.rollback()
        raise Conflict("Another account already uses this IBAN.") from ie
    return Account.model_validate(obj)


def get_account_by_public_id_db(db: Session, public_id: str) -> Account:
    obj = db.scalar(select(AccountORM).where(AccountORM.public_id == public_id))
    if not obj:
        raise NotFound("Account not found.")
    return Account.model_validate(obj)


def get_account_by_iban_hmac_db(db: Session, iban_hmac: str) -> Account:
    obj = db.scalar(select(AccountORM).where(AccountORM.iban_hmac == iban_hmac))
    if not obj:
        raise NotFound("Account not found.")
    return Account.model_validate(obj)


def get_all_accounts_db(
    db: Session, *, name: Optional[str] = None, holder: Optional[str] = None
) -> List[Account]:
    stmt = select(AccountORM).order_by(AccountORM.name.asc())
    if name:
        stmt = stmt.where(AccountORM.name == name)
    if holder:
        stmt = stmt.where(AccountORM.holder_name == holder)
    return [Account.model_validate(r) for r in db.scalars(stmt).all()]
