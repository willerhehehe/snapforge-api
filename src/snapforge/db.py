from __future__ import annotations

import secrets
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "data" / "snapforge.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            stripe_customer_id TEXT UNIQUE,
            tier TEXT NOT NULL DEFAULT 'free',
            requests_limit INTEGER NOT NULL DEFAULT 100,
            requests_used INTEGER NOT NULL DEFAULT 0,
            api_key TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            stripe_subscription_id TEXT UNIQUE NOT NULL,
            stripe_price_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            current_period_end TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.close()


def generate_api_key() -> str:
    return f"sf_{secrets.token_hex(24)}"


def create_customer(email: str, stripe_customer_id: str | None = None, tier: str = "free") -> dict:
    conn = _conn()
    now = datetime.now(timezone.utc).isoformat()
    limits = {"free": 100, "pro": 10000, "business": 100000}
    api_key = generate_api_key()
    conn.execute(
        "INSERT INTO customers (email, stripe_customer_id, tier, requests_limit, api_key, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (email, stripe_customer_id, tier, limits.get(tier, 100), api_key, now, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM customers WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row)


def get_customer_by_email(email: str) -> dict | None:
    conn = _conn()
    row = conn.execute("SELECT * FROM customers WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_customer_by_stripe_id(stripe_customer_id: str) -> dict | None:
    conn = _conn()
    row = conn.execute("SELECT * FROM customers WHERE stripe_customer_id = ?", (stripe_customer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_customer_by_api_key(api_key: str) -> dict | None:
    conn = _conn()
    row = conn.execute("SELECT * FROM customers WHERE api_key = ?", (api_key,)).fetchone()
    conn.close()
    return dict(row) if row else None


def upgrade_customer(stripe_customer_id: str, tier: str):
    limits = {"free": 100, "pro": 10000, "business": 100000}
    now = datetime.now(timezone.utc).isoformat()
    conn = _conn()
    conn.execute(
        "UPDATE customers SET tier = ?, requests_limit = ?, requests_used = 0, updated_at = ? WHERE stripe_customer_id = ?",
        (tier, limits.get(tier, 100), now, stripe_customer_id),
    )
    conn.commit()
    conn.close()


def create_subscription(customer_id: int, stripe_subscription_id: str, stripe_price_id: str, period_end: str | None = None):
    conn = _conn()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO subscriptions (customer_id, stripe_subscription_id, stripe_price_id, status, current_period_end, created_at) VALUES (?, ?, ?, 'active', ?, ?)",
        (customer_id, stripe_subscription_id, stripe_price_id, period_end, now),
    )
    conn.commit()
    conn.close()


def increment_usage(api_key: str) -> bool:
    conn = _conn()
    row = conn.execute("SELECT requests_used, requests_limit FROM customers WHERE api_key = ?", (api_key,)).fetchone()
    if not row:
        conn.close()
        return False
    if row["requests_used"] >= row["requests_limit"]:
        conn.close()
        return False
    conn.execute("UPDATE customers SET requests_used = requests_used + 1 WHERE api_key = ?", (api_key,))
    conn.commit()
    conn.close()
    return True
