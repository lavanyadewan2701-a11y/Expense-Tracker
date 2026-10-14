"""SQLite database helpers for the Personal Expense Tracker."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "expenses.db"
MAX_AMOUNT = 1_000_000_000


def get_connection():
    """Open a SQLite connection with dictionary-like rows."""
    DATABASE_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the transactions table if it does not already exist."""
    with get_connection() as connection:
        connection.execute("DROP TRIGGER IF EXISTS limit_transaction_amount_insert")
        connection.execute("DROP TRIGGER IF EXISTS limit_transaction_amount_update")
        connection.execute("DROP TRIGGER IF EXISTS prevent_negative_balance_insert")
        connection.execute("DROP TRIGGER IF EXISTS prevent_negative_balance_update")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                description TEXT DEFAULT '',
                date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS limit_transaction_amount_insert
            BEFORE INSERT ON transactions
            WHEN NEW.amount <= 0 OR NEW.amount > {MAX_AMOUNT}
            BEGIN
                SELECT RAISE(ABORT, 'transaction amount must be between 0 and 1e9');
            END
            """
        )
        connection.execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS limit_transaction_amount_update
            BEFORE UPDATE OF amount ON transactions
            WHEN NEW.amount <= 0 OR NEW.amount > {MAX_AMOUNT}
            BEGIN
                SELECT RAISE(ABORT, 'transaction amount must be between 0 and 1e9');
            END
            """
        )
        connection.execute(
            """
            CREATE TRIGGER prevent_negative_balance_insert
            BEFORE INSERT ON transactions
            WHEN (SELECT COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END), 0) FROM transactions)
                 + CASE WHEN NEW.type = 'income' THEN NEW.amount ELSE -NEW.amount END < 0
            BEGIN
                SELECT RAISE(ABORT, 'transaction would make the balance negative');
            END
            """
        )
        connection.execute(
            """
            CREATE TRIGGER prevent_negative_balance_update
            BEFORE UPDATE OF type, amount ON transactions
            WHEN (SELECT COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END), 0) FROM transactions WHERE id != NEW.id)
                 + CASE WHEN NEW.type = 'income' THEN NEW.amount ELSE -NEW.amount END < 0
            BEGIN
                SELECT RAISE(ABORT, 'transaction would make the balance negative');
            END
            """
        )
        connection.commit()


def add_transaction(transaction_type, amount, category, description, date):
    """Insert one income or expense using a parameterized query."""
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO transactions (type, amount, category, description, date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (transaction_type, amount, category, description, date),
        )
        connection.commit()


def get_transaction(transaction_id):
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
        ).fetchone()


def get_balance(exclude_id=None):
    """Return the current balance, optionally excluding one transaction for edits."""
    query = "SELECT COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END), 0) FROM transactions"
    parameters = []
    if exclude_id is not None:
        query += " WHERE id != ?"
        parameters.append(exclude_id)
    with get_connection() as connection:
        return connection.execute(query, parameters).fetchone()[0]


def update_transaction(transaction_id, transaction_type, amount, category, description, date):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE transactions
            SET type = ?, amount = ?, category = ?, description = ?, date = ?
            WHERE id = ?
            """,
            (transaction_type, amount, category, description, date, transaction_id),
        )
        connection.commit()


def delete_transaction(transaction_id):
    with get_connection() as connection:
        connection.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        connection.commit()


def get_dashboard_data():
    with get_connection() as connection:
        totals = connection.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses,
                COUNT(*) AS transaction_count
            FROM transactions
            """
        ).fetchone()
        categories = connection.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE type = 'expense'
            GROUP BY category
            ORDER BY total DESC
            """
        ).fetchall()
        recent = connection.execute(
            "SELECT * FROM transactions ORDER BY date DESC, created_at DESC, id DESC LIMIT 8"
        ).fetchall()
    return totals, categories, recent


def get_transactions(filters=None):
    filters = filters or {}
    query = "SELECT * FROM transactions WHERE 1 = 1"
    parameters = []

    if filters.get("search"):
        query += " AND (description LIKE ? OR category LIKE ?)"
        search = f"%{filters['search']}%"
        parameters.extend([search, search])
    if filters.get("category"):
        query += " AND category = ?"
        parameters.append(filters["category"])
    if filters.get("type") in {"income", "expense"}:
        query += " AND type = ?"
        parameters.append(filters["type"])
    if filters.get("date"):
        query += " AND date = ?"
        parameters.append(filters["date"])
    if filters.get("date_from"):
        query += " AND date >= ?"
        parameters.append(filters["date_from"])
    if filters.get("date_to"):
        query += " AND date <= ?"
        parameters.append(filters["date_to"])

    query += " ORDER BY date DESC, created_at DESC, id DESC"
    with get_connection() as connection:
        return connection.execute(query, parameters).fetchall()


def get_categories():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT DISTINCT category FROM transactions ORDER BY category"
        ).fetchall()
    return [row["category"] for row in rows]


def get_category_analysis():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM transactions
            WHERE type = 'expense'
            GROUP BY category
            ORDER BY total DESC
            """
        ).fetchall()
    total = sum(row["total"] for row in rows)
    return [
        {"category": row["category"], "total": row["total"], "percentage": (row["total"] / total * 100 if total else 0)}
        for row in rows
    ]


def get_monthly_analysis():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT substr(date, 1, 7) AS month,
                   COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
                   COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses
            FROM transactions
            GROUP BY substr(date, 1, 7)
            ORDER BY month
            """
        ).fetchall()
    return [
        {"month": row["month"], "income": row["income"], "expenses": row["expenses"], "savings": row["income"] - row["expenses"]}
        for row in rows
    ]
