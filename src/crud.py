from typing import List, Optional, Any, Tuple
from datetime import date
from .database import get_db_connection
from .models import Transaction, TransactionWithCategory, Account, Category
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
        clauses.append("t.date <= ?")
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


def get_category_db(text: str, entity: str) -> Optional[dict]:
    """Retrieves a category by text and entity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM categories WHERE text = ? AND entity = ?", (text, entity)
        )
        return cursor.fetchone()


def create_category_if_not_exists(text: str, entity: str) -> None:
    """
    Adds a new category rule with a null category if it doesn't already exist.
    Existing categories are not touched.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO categories (text, entity, category) VALUES (?, ?, NULL)",
            (text, entity),
        )
        conn.commit()


def create_or_update_category(category: Category) -> None:
    """Adds or updates a category."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO categories (text, entity, category) VALUES (?, ?, ?)",
            (category.text, category.entity, category.category),
        )
        conn.commit()


def get_all_categories_db(
    text: Optional[str] = None, entity: Optional[str] = None
) -> List[dict]:
    """Retrieves all categories."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT * FROM categories WHERE 1=1
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


def update_category_by_text_and_entity_db(
    text: str, entity: str, new_category: str
) -> bool:
    """Updates a specific category rule by text and entity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE categories SET category = ? WHERE text = ? AND entity = ?",
            (new_category, text, entity),
        )
        conn.commit()
        return cursor.rowcount > 0


def update_category_by_entity_db(entity: str, new_category: str) -> int:
    """Updates the category for all rules matching a given entity."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE categories SET category = ? WHERE entity = ?",
            (new_category, entity),
        )
        conn.commit()
        return cursor.rowcount
