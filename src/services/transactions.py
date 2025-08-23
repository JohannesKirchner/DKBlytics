from typing import List, Optional, Any, Tuple
from datetime import date
from ..database import get_db_connection
from ..models import (
    Transaction,
    TransactionWithCategory,
    TransactionSummary,
)
from ..utils import make_fingerprint


# --- Transaction CRUD Operations ---


def get_transaction_by_id(transaction_id: int) -> Optional[dict]:
    """Retrieves a single transaction by its ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,)
        )
        return cursor.fetchone()


def create_transaction_db(transaction: Transaction) -> int:
    """Adds a new transaction to the database and returns its ID."""
    fingerprint = make_fingerprint(
        transaction.text,
        transaction.entity,
        transaction.account,
        transaction.amount,
        transaction.date,
        transaction.reference,
    )
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM transactions WHERE fingerprint = ?", (fingerprint,)
        )
        existing_transaction = cursor.fetchone()
        if existing_transaction:
            return None

        cursor.execute(
            "INSERT INTO transactions (text, entity, account, amount, date, reference, fingerprint) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                transaction.text,
                transaction.entity,
                transaction.account,
                transaction.amount,
                transaction.date,
                transaction.reference,
                fingerprint,
            ),
        )
        conn.commit()
        return cursor.lastrowid


def _build_tx_filters(
    text: Optional[str] = None,
    account: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> Tuple[str, List[Any]]:
    clauses = []
    params: List[Any] = []

    if text:
        clauses.append("(t.text LIKE ? OR t.entity LIKE ?)")
        like = f"%{text}%"
        params.extend([like, like])

    if account:
        clauses.append("t.account = ?")
        params.append(account)

    if category:
        # adjust if your schema stores category differently
        clauses.append("c.category = ?")
        params.append(category)

    if date_from:
        clauses.append("t.date >= ?")
        params.append(str(date_from))  # store ISO yyyy-mm-dd

    if date_to:
        clauses.append("t.date < ?")
        params.append(str(date_to))

    where_sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where_sql, params


def count_transactions_db(
    *,
    text: Optional[str] = None,
    account: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> int:
    where_sql, params = _build_tx_filters(text, account, category, date_from, date_to)
    sql = f"SELECT COUNT(*) FROM transactions t{where_sql};"
    with get_db_connection() as conn:
        cur = conn.execute(sql, params)
        (total,) = cur.fetchone()
    return int(total)


def get_all_transactions_db(
    limit: int,
    offset: int,
    sort: str = "date_desc",
    text: Optional[str] = None,
    account: Optional[str] = None,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> List[dict]:
    """
    Retrieves all transactions with optional filtering,
    joining with the categories table to include the category.
    """
    where_sql, params = _build_tx_filters(text, account, category, date_from, date_to)

    if sort == "date_asc":
        order_by = " ORDER BY date ASC, transaction_id ASC"
    else:
        order_by = " ORDER BY date DESC, transaction_id DESC"

    sql = (
        "SELECT t.*, c.category "
        f"FROM transactions t "
        "LEFT JOIN categories c ON t.text = c.text AND t.entity = c.entity"
        f"{where_sql}"
        f"{order_by} LIMIT ? OFFSET ?;"
    )
    params = params + [limit, offset]

    with get_db_connection() as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()

    items: List[TransactionWithCategory] = []
    for r in rows:
        items.append(
            TransactionWithCategory(
                transaction_id=r["transaction_id"],
                text=r["text"],
                entity=r["entity"],
                account=r["account"],
                amount=r["amount"],
                date=r["date"],  # if stored as ISO yyyy-mm-dd; Pydantic will parse
                reference=r["reference"],
                category=r["category"],
            )
        )
    return items


def get_transactions_summary(
    *,
    group_by_category: bool = True,
    text: Optional[str] = None,
    account: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> List[TransactionSummary]:
    """
    Returns totals grouped by category.
    Category may be None (uncategorized).
    """
    where_sql, params = _build_tx_filters(
        text=text, account=account, category=None, date_from=date_from, date_to=date_to
    )

    sql = (
        "SELECT t.amount, c.category "
        f"FROM transactions t "
        "LEFT JOIN categories c ON t.text = c.text AND t.entity = c.entity"
        f"{where_sql};"
    )

    with get_db_connection() as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()

    totals: dict[Optional[str], TransactionSummary] = {}
    for r in rows:
        if group_by_category:
            cat = r["category"]  # may be None
        else:
            cat = None

        if cat not in totals:
            totals[cat] = TransactionSummary(key=cat, amount_sum=0.0, count=0)
        trow = totals[cat]
        trow.amount_sum += r["amount"]
        trow.count += 1

    # Sort: by absolute sum descending (expenses/income mixed), then name
    result = sorted(
        totals.values(),
        key=lambda x: (abs(x.amount_sum), x.key or ""),
        reverse=True,
    )
    return result
