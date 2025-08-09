import sqlite3
from contextlib import contextmanager
from pathlib import Path


DATABASE_ROOT = "data"
DATABASE_NAME = "banking.db"


@contextmanager
def get_db_connection():
    """
    Context manager to get a database connection.
    Ensures the connection is closed properly.
    """
    db_filepath = Path(DATABASE_ROOT) / DATABASE_NAME

    conn = sqlite3.connect(db_filepath)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    try:
        yield conn
    finally:
        conn.close()


def initialize_database():
    """
    Creates the transactions, accounts, and categories tables if they don't exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create transactions table with the new schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                entity TEXT NOT NULL,
                account TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                reference TEXT,
                fingerprint TEXT NOT NULL
            )
        """)

        # Create accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                name TEXT PRIMARY KEY,
                balance REAL NOT NULL
            )
        """)

        # Create categories table with the new schema and composite primary key
        # cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS categories (
        #         text TEXT NOT NULL,
        #         entity TEXT NOT NULL,
        #         category TEXT NOT NULL,
        #         PRIMARY KEY (text, entity)
        #     )
        # """)
        # conn.commit()
