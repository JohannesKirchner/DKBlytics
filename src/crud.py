from typing import List, Optional, Any, Tuple, Dict
from datetime import date
from .database import get_db_connection
from .models import (
    Transaction,
    TransactionWithCategory,
    TransactionSummary,
    Account,
    Category,
    CategoryRule,
)
from .utils import make_fingerprint


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


# --- Account CRUD Operations ---


def get_account_by_name(account_name: str) -> Optional[dict]:
    """Retrieves the balance for a specific account."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE name = ?", (account_name,))
        return cursor.fetchone()


def create_or_update_account(account: Account) -> None:
    """Adds or updates an account."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO accounts (name, balance) VALUES (?, ?)",
            (account.name, account.balance),
        )
        conn.commit()


def get_all_accounts_db() -> List[dict]:
    """Retrieves all accounts."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts")
        return cursor.fetchall()


def update_account_balance_db(account_name: str, new_balance: float) -> bool:
    """Updates the balance for a specific account."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE accounts SET balance = ? WHERE name = ?",
            (new_balance, account_name),
        )
        conn.commit()
        return cursor.rowcount > 0


# --- Category CRUD Operations ---


def create_category_db(name: str, parent_id: Optional[int]) -> int:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO categories(name, parent_id) VALUES (?, ?);",
            (name, parent_id),
        )
        conn.commit()

        return cursor.fetchone()


def get_all_categories_db() -> List[Category]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, parent_id FROM categories;")
        rows = cursor.fetchall()

        return [Category(**dict(row)) for row in rows]


def build_category_tree(nodes: List[Category]) -> List[Dict]:
    # Build a nested tree in Python for the GET /categories/tree endpoint
    by_id = {n.id: {"id": n.id, "name": n.name, "children": []} for n in nodes}
    roots: List[Dict] = []
    for n in nodes:
        node = by_id[n.id]
        if n.parent_id and n.parent_id in by_id:
            by_id[n.parent_id]["children"].append(node)
        else:
            roots.append(node)

    # stable sort children by name
    def sort_subtree(sub):
        sub["children"].sort(key=lambda x: x["name"].lower())
        for ch in sub["children"]:
            sort_subtree(ch)

    for r in roots:
        sort_subtree(r)
    return roots


def get_category_rule_db(text: str, entity: str) -> Optional[CategoryRule]:
    """Retrieves a category by text and entity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM category_rules WHERE text = ? AND entity = ?", (text, entity)
        )
        return cursor.fetchone()


def create_category_rule_if_not_exists(text: str, entity: str) -> None:
    """
    Adds a new category rule with a null category if it doesn't already exist.
    Existing category rules are not touched.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO category_rules (text, entity, category_id) VALUES (?, ?, NULL)",
            (text, entity),
        )
        conn.commit()


def get_all_category_rules_db(
    text: Optional[str] = None, entity: Optional[str] = None
) -> List[CategoryRule]:
    """Retrieves all category rules."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT * FROM category_rules WHERE 1=1
        """
        params = []

        if text:
            query += " AND text LIKE ?"
            params.append(f"%{text}%")
        if entity:
            query += " AND entity LIKE ?"
            params.append(f"%{entity}%")

        cursor.execute(query, params)
        return cursor.fetchall()


def update_category_rule_by_text_and_entity_db(
    text: str, entity: str, category_id: int
) -> bool:
    """Updates a specific category rule by text and entity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE category_rules SET category_id = ? WHERE text = ? AND entity = ?",
            (category_id, text, entity),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_category_rule_by_entity_db(entity: str, category_id: int) -> int:
    """Updates the category for all rules matching a given entity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE category_rules SET category_id = ? WHERE entity = ?",
            (category_id, entity),
        )
        conn.commit()
        return cursor.rowcount
