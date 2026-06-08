import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "posted.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posted_products (
                product_id TEXT PRIMARY KEY,
                url TEXT,
                posted_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posted_editorials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                posted_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kv (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)


def is_posted(product_id: str) -> bool:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM posted_products WHERE product_id = ?", (product_id,)
        ).fetchone()
    return row is not None


def mark_posted(product_id: str, url: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO posted_products (product_id, url) VALUES (?, ?)",
            (product_id, url),
        )


def log_editorial(topic: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO posted_editorials (topic) VALUES (?)", (topic,)
        )
