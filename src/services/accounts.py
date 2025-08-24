from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Account as AccountORM
from ..schemas import Account


def create_or_update_account(db: Session, account: Account) -> Account:
    obj = db.scalar(select(AccountORM).where(AccountORM.name == account.name))
    if obj is None:
        obj = AccountORM(name=account.name, balance=account.balance)
        db.add(obj)
        db.flush()  # assigns obj.id
    else:
        obj.balance = account.balance
        db.flush()  # assigns obj.id
    return Account.model_validate(obj)


def get_account_by_name(db: Session, account_name: str) -> Optional[Account]:
    obj = db.scalar(select(AccountORM).where(AccountORM.name == account_name))
    return Account.model_validate(obj) if obj else None


def get_all_accounts_db(db: Session) -> List[Account]:
    rows = db.scalars(select(AccountORM).order_by(AccountORM.name.asc())).all()
    return [Account.model_validate(r) for r in rows]
