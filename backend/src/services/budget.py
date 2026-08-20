"""
Budget page aggregations.

Two read endpoints power the budget page:

- `build_sankey_db`  -> the full Income -> Expenses + Savings flow, with the
  category subtrees on both sides. Frontend derives the expense-composition
  donut and the KPI numbers from this same payload.
- `category_series_db` -> a category subtree's summed magnitude per month/year
  across the full history (drives the "over time" panel).

Income vs. expense is structural: every category descends from one of the two
protected roots ("Einnahmen" / "Ausgaben"). `transaction.amount` is signed
(+inflow / -outflow). Uncategorized transactions (`category_id IS NULL`) are
split by sign into "Other income" / "Other".

Savings is NOT a category: it is the synthetic delta `income - expenses`.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..models import (
    Account as AccountORM,
    Category as CategoryORM,
    Transaction as TransactionORM,
)
from ..schemas import (
    CategorySeriesPoint,
    SankeyLink,
    SankeyMeta,
    SankeyNode,
    SankeyResponse,
    SankeyTotals,
)
from ..utils import BadRequest, NotFound
from .categories import ROOT_CATEGORY_NAMES

ZERO = Decimal("0")
INCOME_ROOT, EXPENSE_ROOT = ROOT_CATEGORY_NAMES  # ("Einnahmen", "Ausgaben")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _parse_date(value: Optional[str], *, field: str) -> Optional[dt.date]:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise BadRequest(f"Invalid {field}: expected YYYY-MM-DD.") from exc


def _resolve_account(db: Session, account_id: Optional[str]) -> Optional[str]:
    """Return the validated account public_id, or None for all accounts."""
    if not account_id:
        return None
    acc = db.scalar(select(AccountORM).where(AccountORM.public_id == account_id))
    if acc is None:
        raise NotFound(f"Account '{account_id}' was not found.")
    return acc.public_id


def _tx_conditions(
    *,
    account_id: Optional[str],
    date_from: Optional[dt.date],
    date_to: Optional[dt.date],
) -> list:
    conds = []
    if account_id:
        conds.append(TransactionORM.account_id == account_id)
    if date_from:
        conds.append(TransactionORM.date >= date_from)
    if date_to:
        conds.append(TransactionORM.date <= date_to)
    return conds


def _load_category_tree(
    db: Session,
) -> Tuple[Dict[int, Optional[int]], Dict[int, str], Dict[int, List[int]]]:
    rows = db.execute(
        select(CategoryORM.id, CategoryORM.parent_id, CategoryORM.name)
    ).all()
    parent_by_id: Dict[int, Optional[int]] = {}
    name_by_id: Dict[int, str] = {}
    children_by_id: Dict[int, List[int]] = {}
    for cid, parent_id, name in rows:
        parent_by_id[cid] = parent_id
        name_by_id[cid] = name
        children_by_id.setdefault(cid, [])
        if parent_id is not None:
            children_by_id.setdefault(parent_id, []).append(cid)
    return parent_by_id, name_by_id, children_by_id


def _root_and_depth(cid: int, parent_by_id: Dict[int, Optional[int]]) -> Tuple[int, int]:
    """Return (root_id, depth) where the root has depth 0 and its direct child depth 1."""
    depth = 0
    cur = cid
    while parent_by_id.get(cur) is not None:
        cur = parent_by_id[cur]
        depth += 1
    return cur, depth


def _subtree_ids(start: int, children_by_id: Dict[int, List[int]]) -> List[int]:
    """All category ids in the subtree rooted at `start` (inclusive)."""
    out: List[int] = []
    stack = [start]
    while stack:
        node = stack.pop()
        out.append(node)
        stack.extend(children_by_id.get(node, []))
    return out


# ---------------------------------------------------------------------------
# Sankey
# ---------------------------------------------------------------------------


def build_sankey_db(
    db: Session,
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    account_id: Optional[str] = None,
) -> SankeyResponse:
    start = _parse_date(date_from, field="date_from")
    end = _parse_date(date_to, field="date_to")
    if start and end and start > end:
        raise BadRequest("date_from must be on or before date_to.")
    account = _resolve_account(db, account_id)
    conds = _tx_conditions(account_id=account, date_from=start, date_to=end)

    parent_by_id, name_by_id, children_by_id = _load_category_tree(db)

    # Locate the two protected roots.
    root_id_by_name = {
        name_by_id[cid]: cid
        for cid, pid in parent_by_id.items()
        if pid is None and name_by_id[cid] in (INCOME_ROOT, EXPENSE_ROOT)
    }
    income_root = root_id_by_name.get(INCOME_ROOT)
    expense_root = root_id_by_name.get(EXPENSE_ROOT)

    # Per-category direct sums (categorized only).
    direct: Dict[int, Decimal] = {}
    cat_rows = db.execute(
        select(TransactionORM.category_id, func.sum(TransactionORM.amount))
        .where(TransactionORM.category_id.is_not(None), *conds)
        .group_by(TransactionORM.category_id)
    ).all()
    for cid, total in cat_rows:
        direct[cid] = Decimal(total or 0)

    # Uncategorized split by sign.
    unc_pos, unc_neg = db.execute(
        select(
            func.coalesce(
                func.sum(case((TransactionORM.amount > 0, TransactionORM.amount), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((TransactionORM.amount < 0, TransactionORM.amount), else_=0)),
                0,
            ),
        ).where(TransactionORM.category_id.is_(None), *conds)
    ).one()
    unc_pos = Decimal(unc_pos or 0)
    unc_neg = Decimal(unc_neg or 0)

    # Subtree sums (post-order, memoized).
    subtree: Dict[int, Decimal] = {}

    def calc(cid: int) -> Decimal:
        if cid in subtree:
            return subtree[cid]
        total = direct.get(cid, ZERO)
        for child in children_by_id.get(cid, []):
            total += calc(child)
        subtree[cid] = total
        return total

    for cid in parent_by_id:
        calc(cid)

    # Totals.
    income_total = (subtree.get(income_root, ZERO) if income_root else ZERO) + unc_pos
    expense_total = abs(subtree.get(expense_root, ZERO) if expense_root else ZERO) + abs(unc_neg)
    savings = income_total - expense_total

    nodes: List[SankeyNode] = []
    links: List[SankeyLink] = []

    def group_of(cid: int, depth: int) -> str:
        cur = cid
        d = depth
        while d > 1:
            cur = parent_by_id[cur]
            d -= 1
        return f"cat:{cur}"

    # Category nodes + links (skip empty subtrees and the roots themselves).
    for cid in parent_by_id:
        if cid in (income_root, expense_root):
            continue
        value = abs(subtree.get(cid, ZERO))
        if value == 0:
            continue
        root, depth = _root_and_depth(cid, parent_by_id)
        if root == income_root:
            side = "income"
            parent_node = "income" if depth == 1 else f"cat:{parent_by_id[cid]}"
            links.append(SankeyLink(source=f"cat:{cid}", target=parent_node, value=value))
        elif root == expense_root:
            side = "expense"
            parent_node = "expenses" if depth == 1 else f"cat:{parent_by_id[cid]}"
            links.append(SankeyLink(source=parent_node, target=f"cat:{cid}", value=value))
        else:
            continue  # category not under a known root
        nodes.append(
            SankeyNode(
                id=f"cat:{cid}",
                label=name_by_id[cid],
                side=side,
                depth=depth,
                group=group_of(cid, depth),
            )
        )

    # Synthetic core nodes.
    if income_total > 0:
        nodes.append(SankeyNode(id="income", label="Income", side="income", depth=0, group=None))
    if expense_total > 0:
        nodes.append(SankeyNode(id="expenses", label="Expenses", side="expense", depth=0, group=None))

    if income_total > 0 and expense_total > 0:
        links.append(SankeyLink(source="income", target="expenses", value=expense_total))

    # Savings only when income covers expenses (deficit handling deferred).
    if savings > 0:
        nodes.append(SankeyNode(id="savings", label="Savings", side="income", depth=0, group=None))
        links.append(SankeyLink(source="income", target="savings", value=savings))

    # Uncategorized buckets.
    if unc_pos > 0:
        nodes.append(SankeyNode(id="other_in", label="Other income", side="income", depth=1, group=None))
        links.append(SankeyLink(source="other_in", target="income", value=unc_pos))
    if unc_neg < 0:
        nodes.append(SankeyNode(id="other_out", label="Other", side="expense", depth=1, group=None))
        links.append(SankeyLink(source="expenses", target="other_out", value=abs(unc_neg)))

    # months_with_data
    month_expr = func.strftime("%Y-%m", TransactionORM.date)
    months_with_data = (
        db.scalar(select(func.count(func.distinct(month_expr))).where(*conds)) or 0
    )

    return SankeyResponse(
        nodes=nodes,
        links=links,
        totals=SankeyTotals(income=income_total, expenses=expense_total, savings=savings),
        meta=SankeyMeta(months_with_data=months_with_data),
    )


# ---------------------------------------------------------------------------
# Category time series
# ---------------------------------------------------------------------------


def category_series_db(
    db: Session,
    *,
    category_id: str,
    account_id: Optional[str] = None,
    granularity: str = "monthly",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[CategorySeriesPoint]:
    if granularity not in ("monthly", "yearly"):
        raise BadRequest("granularity must be 'monthly' or 'yearly'.")
    account = _resolve_account(db, account_id)

    # Category filter (subtree, or uncategorized).
    if category_id == "uncategorized":
        cat_cond = TransactionORM.category_id.is_(None)
    else:
        try:
            cid = int(category_id)
        except (TypeError, ValueError) as exc:
            raise BadRequest("category_id must be an integer or 'uncategorized'.") from exc
        if db.get(CategoryORM, cid) is None:
            raise NotFound(f"Category with id {cid} was not found.")
        _, _, children_by_id = _load_category_tree(db)
        cat_cond = TransactionORM.category_id.in_(_subtree_ids(cid, children_by_id))

    account_conds = _tx_conditions(account_id=account, date_from=None, date_to=None)

    # X-axis spans the whole history (account-filtered), independent of category.
    start = _parse_date(date_from, field="date_from")
    end = _parse_date(date_to, field="date_to")
    if start is None or end is None:
        mn, mx = db.execute(
            select(func.min(TransactionORM.date), func.max(TransactionORM.date)).where(
                *account_conds
            )
        ).one()
        if mn is None:
            return []
        start = start or _ensure_date(mn)
        end = end or _ensure_date(mx)

    fmt = "%Y-%m" if granularity == "monthly" else "%Y"
    bucket_expr = func.strftime(fmt, TransactionORM.date)
    rows = db.execute(
        select(bucket_expr, func.sum(TransactionORM.amount))
        .where(cat_cond, *account_conds, TransactionORM.date >= start, TransactionORM.date <= end)
        .group_by(bucket_expr)
    ).all()
    sums = {key: Decimal(val or 0) for key, val in rows}

    points: List[CategorySeriesPoint] = []
    for bucket_start in _iter_buckets(start, end, granularity):
        key = bucket_start.strftime(fmt)
        points.append(
            CategorySeriesPoint(date=bucket_start, value=abs(sums.get(key, ZERO)))
        )
    return points


def _iter_buckets(start: dt.date, end: dt.date, granularity: str) -> List[dt.date]:
    out: List[dt.date] = []
    if granularity == "yearly":
        for year in range(start.year, end.year + 1):
            out.append(dt.date(year, 1, 1))
        return out
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        out.append(dt.date(year, month, 1))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return out


def _ensure_date(value) -> dt.date:
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value))
