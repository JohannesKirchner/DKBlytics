from typing import List, Optional  # , Dict, Any
from datetime import date
from .database import get_db_connection
from .models import Transaction, Account  # , Category
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


def get_all_transactions_db(
    text: Optional[str] = None,
    account: Optional[str] = None,
    min_date: Optional[date] = None,
    max_date: Optional[date] = None,
) -> List[dict]:
    """Retrieves all transactions with optional filtering."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if text:
            query += " AND text LIKE ?"
            params.append(f"%{text}%")
        if account:
            query += " AND account = ?"
            params.append(account)
        if min_date:
            query += " AND date >= ?"
            params.append(min_date)
        if max_date:
            query += " AND date <= ?"
            params.append(max_date)

        cursor.execute(query, params)
        return cursor.fetchall()


# def update_transaction_db(transaction_id: int, update_data: Dict[str, Any]) -> bool:
#     """Updates an existing transaction by ID."""
#     with get_db_connection() as conn:
#         cursor = conn.cursor()
#         set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
#         params = list(update_data.values())
#         params.append(transaction_id)

#         cursor.execute(
#             f"UPDATE transactions SET {set_clause} WHERE transaction_id = ?", params
#         )
#         conn.commit()
#         return cursor.rowcount > 0


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


# def get_category_db(text: str, entity: str) -> Optional[dict]:
#     """Retrieves a category by text and entity."""
#     with get_db_connection() as conn:
#         cursor = conn.cursor()
#         cursor.execute(
#             "SELECT * FROM categories WHERE text = ? AND entity = ?", (text, entity)
#         )
#         return cursor.fetchone()


# def create_or_update_category(category: Category) -> None:
#     """Adds or updates a category."""
#     with get_db_connection() as conn:
#         cursor = conn.cursor()
#         cursor.execute(
#             "INSERT OR REPLACE INTO categories (text, entity, category) VALUES (?, ?, ?)",
#             (category.text, category.entity, category.category),
#         )
#         conn.commit()


# def get_all_categories_db() -> List[dict]:
#     """Retrieves all categories."""
#     with get_db_connection() as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM categories")
#         return cursor.fetchall()


# def update_category_db(text: str, entity: str, new_category: str) -> bool:
#     """Updates a category by text and entity."""
#     with get_db_connection() as conn:
#         cursor = conn.cursor()
#         cursor.execute(
#             "UPDATE categories SET category = ? WHERE text = ? AND entity = ?",
#             (new_category, text, entity),
#         )
#         conn.commit()
#         return cursor.rowcount > 0
