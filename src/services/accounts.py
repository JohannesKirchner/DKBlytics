from typing import List, Optional
from ..database import get_db_connection
from ..models import Account


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

        return cursor.lastrowid


def get_all_accounts_db() -> List[dict]:
    """Retrieves all accounts."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts")

        return cursor.fetchall()
