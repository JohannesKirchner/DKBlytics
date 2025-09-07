from typing import List, Optional, Tuple, Dict
from decimal import Decimal
from collections import defaultdict

from sqlalchemy import select, or_, and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import Select

from ..models import (
    Transaction as TransactionORM,
    Account as AccountORM,
    Category as CategoryORM,
)
from ..schemas import (
    Transaction,
    TransactionCreate,
    TransactionUpdate,
    TransactionSummary,
    PaginatedTransactions,
)
from ..utils import make_fingerprint, Conflict, NotFound, BadRequest
from .category_rules import resolve_category_for_db, _resolve_category_for_db_orm
from .categories import _find_unique_category_by_name


# ---- Helpers ----------------------------------------------------------------


# def _quantize_amount(value: Decimal) -> str:
#    """Return a canonical string for Decimal with 2 dp, rounding half up."""
#    return str(value.quantize(Decimal("0.01"), rounding="ROUND_HALF_UP"))


def _tx_to_schema(
    row: TransactionORM,
    *,
    account_name: str,
    account_id: str,
    category_name: Optional[str],
) -> Transaction:
    return Transaction(
        id=row.id,
        text=getattr(row, "text", None),
        entity=row.entity or "",
        account_name=account_name,
        account_id=account_id,
        amount=row.amount,
        date=row.date,
        reference=getattr(row, "reference", None),
        batch_hash=getattr(row, "batch_hash", None),
        fingerprint=row.fingerprint,
        category=category_name,
    )


def _build_category_indexes(db: Session) -> Tuple[Dict[int, int], Dict[int, str]]:
    """Return (parent_by_id, name_by_id)."""
    rows = db.scalars(select(CategoryORM)).all()
    parent_by_id = {r.id: r.parent_id for r in rows}
    name_by_id = {r.id: r.name for r in rows}
    return parent_by_id, name_by_id


def _ancestor_at_scope_depth(
    node_id: int,
    parent_by_id: Dict[int, Optional[int]],
    scope_id: Optional[int],
    depth: int,
) -> Optional[int]:
    """
    Return the ancestor category id at 'depth' below 'scope_id'.

    - scope_id=None means a virtual root whose children are the DB root categories.
    - depth=1 means direct children of the scope.
    - If the node is not within the scope subtree, returns None.
    - If the node doesn't reach the requested depth, returns the deepest available ancestor
      within the scope chain (so shallow categories still get counted).
    """
    # Build full chain from node up to real root: [node, parent, ..., None]
    chain: List[int] = []
    cur = node_id
    while cur is not None:
        chain.append(cur)
        cur = parent_by_id.get(cur)

    # Reverse to get path from real root -> node
    path_root_to_node = list(reversed(chain))  # [root, ..., node]

    if scope_id is None:
        # virtual root: scope lies before first real root
        scope_index = -1  # virtual
    else:
        try:
            scope_index = path_root_to_node.index(scope_id)
        except ValueError:
            return None  # node not in scope subtree

    target_index = scope_index + depth  # index in path_root_to_node
    # If too deep, clamp to last existing
    if target_index >= len(path_root_to_node):
        target_index = len(path_root_to_node) - 1
    if target_index < 0:
        return None

    return path_root_to_node[target_index]


def _get_transaction_select(
    db: Session,
    *,
    sort_by: str = "date_desc",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    account_id: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,  # substring search across entity/text/reference
) -> Select:
    if sort_by not in SortBy:
        raise BadRequest(f"Unsupported sort_by '{sort_by}'.")

    tx = TransactionORM
    q_stmt = select(tx).options(joinedload(tx.account))

    conds = []
    if date_from:
        conds.append(tx.date >= date_from)
    if date_to:
        conds.append(tx.date <= date_to)
    if category is None:
        # No filter → all transactions
        pass
    elif category.lower() == "null":
        # Only uncategorized
        conds.append(tx.category_id.is_(None))
    else:
        # Only a specific category
        q_stmt = q_stmt.join(tx.category).where(CategoryORM.name == category)
    if account_id:
        acc = db.scalar(select(AccountORM).where(AccountORM.public_id == account_id))
        if acc is None:
            raise NotFound(f"Couldn't find account with ID {account_id}")
        conds.append(tx.account_id == acc.id)
    if q:
        pattern = f"%{q.lower()}%"
        entity_ci = func.lower(tx.entity).like(pattern)
        clauses = [entity_ci]
        clauses.append(func.lower(tx.text).like(pattern))
        clauses.append(func.lower(tx.reference).like(pattern))
        conds.append(or_(*clauses))

    if conds:
        q_stmt = q_stmt.where(and_(*conds))

    if sort_by == "date_desc":
        q_stmt = q_stmt.order_by(tx.date.desc(), tx.id.desc())
    elif sort_by == "date_asc":
        q_stmt = q_stmt.order_by(tx.date.asc(), tx.id.asc())
    elif sort_by == "amount_desc":
        q_stmt = q_stmt.order_by(tx.amount.desc(), tx.id.desc())
    elif sort_by == "amount_asc":
        q_stmt = q_stmt.order_by(tx.amount.asc(), tx.id.asc())

    return q_stmt


# ---- Create -----------------------------------------------------------------


def create_transaction_db(db: Session, payload: TransactionCreate) -> Transaction:
    # 1) Resolve account
    account = db.scalar(
        select(AccountORM).where(AccountORM.public_id == payload.account_id)
    )
    if account is None:
        raise NotFound(f"Account '{payload.account}' was not found.")

    # 2) Compute fingerprint
    fingerprint = make_fingerprint(
        text=payload.text,
        entity=payload.entity,
        account=account.public_id,
        amount=payload.amount,
        date=payload.date,
        reference=payload.reference,
    )

    # 3) Enforce your batch-aware de-dup rule in app logic:
    #    allow duplicates only when (fingerprint, batch_hash) match exactly.
    existing = db.scalars(
        select(TransactionORM).where(TransactionORM.fingerprint == fingerprint)
    ).all()
    for e in existing:
        if getattr(e, "batch_hash", None) != payload.batch_hash:
            raise Conflict(
                "Duplicate transaction: fingerprint already exists with a different batch_hash."
            )
    # Otherwise: either none exist, or all have the same batch_hash -> allowed.

    # 4) Insert
    obj = TransactionORM(
        text=payload.text,
        entity=payload.entity,
        account_id=account.public_id,
        date=payload.date,
        amount=payload.amount,
        reference=payload.reference,
        batch_hash=payload.batch_hash,
        fingerprint=fingerprint,
    )

    try:
        db.add(obj)
        db.flush()  # assigns obj.id
    except IntegrityError as ie:
        # We no longer rely on a unique constraint for fingerprint,
        # but keep this as a safeguard for other constraints.
        db.rollback()
        raise Conflict(
            "Could not create transaction due to a constraint violation."
        ) from ie

    # 5) Resolve category
    cat_name = resolve_category_for_db(db, entity=payload.entity, text=payload.text)

    return _tx_to_schema(
        obj,
        account_name=account.name,
        account_id=account.public_id,
        category_name=cat_name,
    )


# ---- Read one ---------------------------------------------------------------


def get_transaction_db(db: Session, tx_id: int) -> Transaction:
    row = db.scalar(
        select(TransactionORM)
        .options(joinedload(TransactionORM.account))
        .where(TransactionORM.id == tx_id)
    )
    if row is None:
        raise NotFound(f"Transaction {tx_id} was not found.")

    cat_name = resolve_category_for_db(db, entity=row.entity, text=row.text or "")

    return _tx_to_schema(
        row,
        account_name=row.account.name,
        account_id=row.account.public_id,
        category_name=cat_name,
    )


# ---- Update -----------------------------------------------------------------


def update_transaction_db(db: Session, tx_id: int, payload: TransactionUpdate) -> Transaction:
    """
    Update transaction entity and/or text fields while preserving the original fingerprint.
    
    This allows manual correction of generic bank transaction descriptions
    while maintaining deduplication integrity based on the original raw data.
    """
    # 1) Find existing transaction
    row = db.scalar(
        select(TransactionORM)
        .options(joinedload(TransactionORM.account))
        .where(TransactionORM.id == tx_id)
    )
    if row is None:
        raise NotFound(f"Transaction {tx_id} was not found.")

    # 2) Update only the fields that were provided (not None)
    has_changes = False
    if payload.entity is not None and payload.entity != row.entity:
        row.entity = payload.entity
        has_changes = True
    if payload.text is not None and payload.text != row.text:
        row.text = payload.text
        has_changes = True

    # 3) If no changes, just return current state
    if not has_changes:
        cat_name = resolve_category_for_db(db, entity=row.entity, text=row.text or "")
        return _tx_to_schema(
            row,
            account_name=row.account.name,
            account_id=row.account.public_id,
            category_name=cat_name,
        )

    # 4) Save changes (fingerprint remains unchanged)
    try:
        db.flush()
    except IntegrityError as ie:
        db.rollback()
        raise Conflict("Could not update transaction due to a constraint violation.") from ie

    # 5) Resolve updated category and return
    cat_name = resolve_category_for_db(db, entity=row.entity, text=row.text or "")
    
    return _tx_to_schema(
        row,
        account_name=row.account.name,
        account_id=row.account.public_id,
        category_name=cat_name,
    )


# ---- List with filters/pagination -------------------------------------------

SortBy = ("date_desc", "date_asc", "amount_desc", "amount_asc")


def list_transactions_db(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "date_desc",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    account_id: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,  # substring search across entity/text/reference
) -> PaginatedTransactions:
    if sort_by not in SortBy:
        raise BadRequest(f"Unsupported sort_by '{sort_by}'.")

    q_stmt = _get_transaction_select(
        db,
        sort_by=sort_by,
        date_from=date_from,
        date_to=date_to,
        account_id=account_id,
        category=category,
        q=q,
    )

    total = db.scalar(select(func.count()).select_from(q_stmt.subquery())) or 0
    q_stmt = q_stmt.limit(limit).offset(offset)
    rows: List[TransactionORM] = db.scalars(q_stmt).all()

    items: List[Transaction] = []
    for r in rows:
        cat_name = resolve_category_for_db(db, entity=r.entity, text=r.text)
        items.append(
            _tx_to_schema(
                r,
                account_name=r.account.name,
                account_id=r.account.public_id,
                category_name=cat_name,
            )
        )

    return PaginatedTransactions(items=items, total=total, limit=limit, offset=offset)


# ---- Summary by category at scope/depth -------------------------------------


def summarize_by_category_db(
    db: Session,
    *,
    scope_name: Optional[str] = None,
    depth: int = 1,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    account_id: Optional[str] = None,
    q: Optional[str] = None,
) -> List[TransactionSummary]:
    """
    Summarize by category nodes at a given depth within a scope subtree.

    - scope_name=None, depth=1  -> root categories
    - scope_name="Expenses", 1  -> direct children of Expenses
    - scope_name="Expenses", 2  -> grandchildren of Expenses
    - If a resolved transaction category is shallower than the requested depth within the scope,
      it is grouped under its deepest available ancestor (so shallow nodes are not dropped).
    - You can filter by account/date/q; there is no separate "group by account".
    """

    # Determine scope_id
    scope_id: Optional[int] = None
    if scope_name:
        scope_id = _find_unique_category_by_name(db, scope_name).id

    # Fetch candidate transactions
    q_stmt = _get_transaction_select(
        db, date_from=date_from, date_to=date_to, account_id=account_id, q=q
    )
    rows: List[TransactionORM] = db.scalars(q_stmt).all()

    # Build category indexes
    parent_by_id, name_by_id = _build_category_indexes(db)

    # Aggregate
    sums: Dict[Optional[str], Decimal] = defaultdict(lambda: Decimal("0"))
    bucket_items: Dict[Optional[str], List[Transaction]] = defaultdict(list)
    for r in rows:
        cat_row = _resolve_category_for_db_orm(db, entity=r.entity, text=r.text or "")
        if not cat_row:
            group_name = None  # uncategorized
            cat_name = None
        else:
            group_id = _ancestor_at_scope_depth(
                cat_row.id, parent_by_id, scope_id, depth
            )
            if group_id is None:
                # outside scope; skip
                continue
            group_name = name_by_id[group_id]
            cat_name = cat_row.name

        # Convert row to API schema with resolved category
        tx_schema = _tx_to_schema(
            r,
            account_name=r.account.name,
            account_id=r.account.public_id,
            category_name=cat_name,
        )

        # Aggregate
        sums[group_name] += r.amount
        bucket_items[group_name].append(tx_schema)

    # Format output
    results: List[TransactionSummary] = []
    for name, txs in bucket_items.items():
        results.append(
            TransactionSummary(key=name, amount_sum=sums[name], transactions=txs)
        )

    # Sort by absolute amount desc, then number of transactions
    results.sort(key=lambda x: (abs(x.amount_sum), len(x.transactions)), reverse=True)
    return results
