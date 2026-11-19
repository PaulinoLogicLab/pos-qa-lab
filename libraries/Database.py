"""Robot library: read-only assertions against the API database."""

from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_DB = ROOT / "data" / "pos_qa.db"


class Database:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or os.getenv("POS_QA_DB", str(DEFAULT_DB)))

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        return conn

    def get_payment(self, payment_id: str):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
            return dict(row) if row else None

    def count_payments_by_idempotency(self, idempotency_key: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM payments WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            return int(row["total"])

    def count_all_payments(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS total FROM payments").fetchone()
            return int(row["total"])

    def get_events(self, payment_id: str):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT event_type, from_status, to_status, amount_cents, correlation_id "
                "FROM payment_events WHERE payment_id = ? ORDER BY id",
                (payment_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_refunds(self, payment_id: str):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT amount_cents, correlation_id FROM refunds "
                "WHERE payment_id = ? ORDER BY created_at",
                (payment_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def get_settlement(self, settlement_id: str):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM settlements WHERE id = ?", (settlement_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_settlement_items(self, settlement_id: str):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payment_id, gross_cents, refunded_cents, net_cents "
                "FROM settlement_items WHERE settlement_id = ? ORDER BY id",
                (settlement_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def count_settlements_by_idempotency(self, idempotency_key: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM settlements WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            return int(row["total"])
