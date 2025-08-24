from typing import List, Optional, Tuple
from datetime import date
from decimal import Decimal
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session
from ..models import (
    Transaction as TransactionORM,
    Account as AccountORM,
    Category as CategoryORM,
    CategoryRule as CategoryRuleORM,
)
from ..schemas import (
    Transaction,
    TransactionSummary,
)
from ..utils import make_fingerprint


def _to_tx_schema(
    row: Tuple[TransactionORM, Optional[str], Optional[int]],
) -> Transaction:
    tx, account_name, _ = (
        row  # third part may be category_id (not exposed directly here)
    )
    return Transaction(
        id=tx.id,
        text=tx.text,
        entity=tx.entity,
        account=account_name or "",  # preserve API shape as account name
        amount=tx.amount,
        date=tx.date,
        reference=tx.reference,
    )


def create_transaction_db(db: Session, tx: Transaction) -> bool:
    # ensure account exists (by name)
    acct = db.execute(
        select(AccountORM).where(AccountORM.name == tx.account)
    ).scalar_one_or_none()
    if acct is None:
        acct = AccountORM(name=tx.account, balance=0)
        db.add(acct)
        db.flush()  # get id

    fingerprint = make_fingerprint(
        tx.text, tx.entity, tx.account, tx.amount, tx.date, tx.reference
    )

    exists = db.execute(
        select(TransactionORM.id).where(TransactionORM.fingerprint == fingerprint)
    ).first()
    if exists:
        db.rollback()  # in case we created an account in this transaction intentionally keep it
        return False

    obj = TransactionORM(
        text=tx.text,
        entity=tx.entity,
        account_id=acct.id,
        amount=tx.amount,
        date=tx.date,
        reference=tx.reference,
        fingerprint=fingerprint,
    )
    db.add(obj)

    return True


def get_transaction_by_id(db: Session, tx_id: int) -> Optional[Transaction]:
    stmt = (
        select(TransactionORM, AccountORM.name)
        .join(AccountORM, TransactionORM.account_id == AccountORM.id)
        .where(TransactionORM.id == tx_id)
    )
    row = db.execute(stmt).first()
    if not row:
        return None
    return _to_tx_schema(row)


def _filters_stmt(
    *,
    text: Optional[str],
    category: Optional[str],
    account: Optional[str],
    date_from: Optional[date],
    date_to: Optional[date],
    q: Optional[str],
):
    # Build a SQLAlchemy expression for filters to reuse in count/list queries
    filters = []
    if text:
        filters.append(TransactionORM.text == text)
    if account:
        filters.append(AccountORM.name == account)
    if date_from:
        filters.append(TransactionORM.date >= date_from)
    if date_to:
        filters.append(TransactionORM.date < date_to)
    if q:
        like = f"%{q}%"
        filters.append(
            or_(TransactionORM.text.ilike(like), TransactionORM.entity.ilike(like))
        )
    # category via category_rules
    if category:
        filters.append(
            select(CategoryORM.id)
            .join(CategoryRuleORM, CategoryRuleORM.category_id == CategoryORM.id)
            .where(
                CategoryORM.name == category,
                CategoryRuleORM.text == TransactionORM.text,
                CategoryRuleORM.entity == TransactionORM.entity,
            )
            .exists()
        )
    return filters


def count_transactions_db(
    db: Session,
    *,
    text: Optional[str] = None,
    category: Optional[str] = None,
    account: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
) -> int:
    filters = _filters_stmt(
        text=text,
        category=category,
        account=account,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )
    stmt = select(func.count(TransactionORM.id)).join(
        AccountORM, TransactionORM.account_id == AccountORM.id
    )
    for f in filters:
        stmt = stmt.where(f)
    return db.execute(stmt).scalar_one()


def get_all_transactions_db(
    db: Session,
    *,
    limit: int,
    offset: int,
    sort_by: str = "date_desc",
    text: Optional[str] = None,
    category: Optional[str] = None,
    account: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    q: Optional[str] = None,
) -> List[Transaction]:
    filters = _filters_stmt(
        text=text,
        category=category,
        account=account,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )

    stmt = (
        select(TransactionORM, AccountORM.name, CategoryRuleORM.category_id)
        .join(AccountORM, TransactionORM.account_id == AccountORM.id)
        .outerjoin(
            CategoryRuleORM,
            (CategoryRuleORM.text == TransactionORM.text)
            & (CategoryRuleORM.entity == TransactionORM.entity),
        )
    )
    for f in filters:
        stmt = stmt.where(f)

    if sort_by in ("date_desc", "date"):
        stmt = stmt.order_by(TransactionORM.date.desc())
    elif sort_by == "date_asc":
        stmt = stmt.order_by(TransactionORM.date.asc())
    elif sort_by == "amount_desc":
        stmt = stmt.order_by(TransactionORM.amount.desc())
    elif sort_by == "amount_asc":
        stmt = stmt.order_by(TransactionORM.amount.asc())
    else:
        stmt = stmt.order_by(TransactionORM.date.desc())

    stmt = stmt.limit(limit).offset(offset)

    rows = db.execute(stmt).all()
    return [_to_tx_schema(r) for r in rows]


def get_transactions_summary(
    db: Session,
    *,
    by: str = "category",  # category | account | entity | month
    account: Optional[str] = None,
    q: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> TransactionSummary:
    filters = _filters_stmt(
        text=None,
        category=None,
        account=account,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )

    if by == "account":
        key_expr = AccountORM.name
        join_rules = False
    elif by == "entity":
        key_expr = TransactionORM.entity
        join_rules = False
    elif by == "month":
        # YYYY-MM
        key_expr = func.strftime("%Y-%m", TransactionORM.date)
        join_rules = False
    else:  # "category"
        key_expr = func.coalesce(CategoryORM.name, "Uncategorized")
        join_rules = True

    stmt = (
        select(
            key_expr.label("grp"),
            func.count().label("cnt"),
            func.sum(TransactionORM.amount).label("total"),
        )
        .select_from(TransactionORM)
        .join(AccountORM, TransactionORM.account_id == AccountORM.id)
    )

    if join_rules:
        stmt = stmt.outerjoin(
            CategoryRuleORM,
            (CategoryRuleORM.text == TransactionORM.text)
            & (CategoryRuleORM.entity == TransactionORM.entity),
        ).outerjoin(CategoryORM, CategoryORM.id == CategoryRuleORM.category_id)

    for f in filters:
        stmt = stmt.where(f)

    stmt = stmt.group_by("grp").order_by(func.sum(TransactionORM.amount).desc())

    items = [
        TransactionSummary(
            group=row.grp, count=row.cnt, total=row.total or Decimal("0.00")
        )
        for row in db.execute(stmt)
    ]
    return TransactionSummary(
        by=by if by in {"category", "account", "entity", "month"} else "category",
        items=items,
    )
