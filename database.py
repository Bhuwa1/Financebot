import sqlite3
import os
from datetime import datetime, date
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "finance_tracker.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('expense', 'income', 'investment')),
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def add_transaction(
    user_id: int,
    tx_type: str,
    amount: float,
    category: str,
    description: Optional[str],
    tx_date: Optional[str] = None,
) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    if tx_date is None:
        tx_date = date.today().isoformat()

    cursor.execute(
        """
        INSERT INTO transactions (user_id, type, amount, category, description, date, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, tx_type, amount, category, description, tx_date, now),
    )

    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tx_id


def get_summary(user_id: int, period: str = "month") -> dict:
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today()

    if period == "today":
        date_filter = today.isoformat()
        date_clause = "AND date = ?"
        params_base = [user_id, date_filter]
    elif period == "week":
        from datetime import timedelta
        week_start = (today - timedelta(days=today.weekday())).isoformat()
        date_clause = "AND date >= ?"
        params_base = [user_id, week_start]
    elif period == "month":
        month_start = today.replace(day=1).isoformat()
        date_clause = "AND date >= ?"
        params_base = [user_id, month_start]
    elif period == "year":
        year_start = today.replace(month=1, day=1).isoformat()
        date_clause = "AND date >= ?"
        params_base = [user_id, year_start]
    else:
        date_clause = ""
        params_base = [user_id]

    def query_totals(tx_type):
        cursor.execute(
            f"""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ? AND type = ? {date_clause}
            """,
            [user_id, tx_type] + (params_base[1:] if date_clause else []),
        )
        return cursor.fetchone()["total"]

    def query_by_category(tx_type):
        cursor.execute(
            f"""
            SELECT category, SUM(amount) as total, COUNT(*) as count
            FROM transactions
            WHERE user_id = ? AND type = ? {date_clause}
            GROUP BY category
            ORDER BY total DESC
            """,
            [user_id, tx_type] + (params_base[1:] if date_clause else []),
        )
        return cursor.fetchall()

    def query_recent(tx_type, limit=5):
        cursor.execute(
            f"""
            SELECT amount, category, description, date
            FROM transactions
            WHERE user_id = ? AND type = ? {date_clause}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [user_id, tx_type] + (params_base[1:] if date_clause else []) + [limit],
        )
        return cursor.fetchall()

    result = {
        "expenses": {
            "total": query_totals("expense"),
            "by_category": [dict(r) for r in query_by_category("expense")],
            "recent": [dict(r) for r in query_recent("expense")],
        },
        "income": {
            "total": query_totals("income"),
            "by_category": [dict(r) for r in query_by_category("income")],
            "recent": [dict(r) for r in query_recent("income")],
        },
        "investments": {
            "total": query_totals("investment"),
            "by_category": [dict(r) for r in query_by_category("investment")],
            "recent": [dict(r) for r in query_recent("investment")],
        },
    }

    conn.close()
    return result


def get_recent_transactions(user_id: int, limit: int = 10) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT type, amount, category, description, date
        FROM transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
