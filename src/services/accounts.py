from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Account as AccountORM
from ..schemas import Account, AccountCreate
from .utils import Conflict, NotFound, BadRequest


def create_account_db(db: Session, payload: AccountCreate) -> Account:
    """
    Create a new account with a unique name.
    Raises Conflict if an account with the same name already exists.
    """
    obj = AccountORM(name=payload.name, balance=payload.balance)
    try:
        db.add(obj)
        db.flush()  # assigns obj.id
    except IntegrityError as ie:
        db.rollback()
        # hits when unique constraint on name is violated
        raise Conflict(f"Account '{payload.name}' already exists.") from ie
    return Account.model_validate(obj)


def update_account_db(
    db: Session, account_name: str, payload: AccountCreate
) -> Account:
    """
    Update an existing account's balance.

    - Requires that payload.name matches the path parameter (defensive).
    - Raises NotFound if the account does not exist.
    - Raises BadRequest if names do not match.
    """
    if payload.name != account_name:
        raise BadRequest("Body.name must match path account_name.")

    obj = db.scalar(select(AccountORM).where(AccountORM.name == account_name))
    if obj is None:
        raise NotFound(f"Account '{account_name}' was not found.")

    obj.balance = payload.balance
    db.flush()
    return Account.model_validate(obj)


def get_account_by_name_db(db: Session, account_name: str) -> Account:
    obj = db.scalar(select(AccountORM).where(AccountORM.name == account_name))
    if obj is None:
        raise NotFound(f"Account '{account_name}' was not found.")
    return Account.model_validate(obj)


def get_all_accounts_db(db: Session) -> List[Account]:
    rows = db.scalars(select(AccountORM).order_by(AccountORM.name.asc())).all()
    return [Account.model_validate(r) for r in rows]
