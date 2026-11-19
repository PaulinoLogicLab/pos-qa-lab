"""SQLite persistence for the simulated payment API."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "pos_qa.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_hash TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    currency TEXT NOT NULL,
    method TEXT NOT NULL,
    installments INTEGER NOT NULL,
    entry_mode TEXT NOT NULL,
    terminal_id TEXT NOT NULL,
    merchant_id TEXT NOT NULL,
    card_token TEXT NOT NULL,
    capture_requested INTEGER NOT NULL,
    status TEXT NOT NULL,
    response_code TEXT NOT NULL,
    http_status INTEGER NOT NULL,
    refunded_cents INTEGER NOT NULL DEFAULT 0,
    correlation_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payment_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    from_status TEXT,
    to_status TEXT,
    amount_cents INTEGER,
    correlation_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (payment_id) REFERENCES payments(id)
);

CREATE TABLE IF NOT EXISTS refunds (
    id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    correlation_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (payment_id) REFERENCES payments(id)
);
"""


def db_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    return Path(os.getenv("POS_QA_DB", str(DEFAULT_DB)))


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    target = db_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: str | Path | None = None) -> None:
    with connect(path) as conn:
        conn.executescript(SCHEMA)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
