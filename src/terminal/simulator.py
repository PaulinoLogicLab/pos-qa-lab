"""Terminal simulator used by the Robot suites.

The simulator keeps an offline queue in SQLite so a restart can be tested
without a real POS. It talks to the simulated API over HTTP.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

import requests

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_DIR = ROOT / "data"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _money(value: str | float | Decimal) -> str:
    return f"{Decimal(str(value)).quantize(Decimal('0.01')):.2f}"


class TerminalSimulator:
    def __init__(
        self,
        api_url: str = "http://127.0.0.1:8000",
        terminal_id: str = "TERM0001",
        db_path: str | None = None,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.terminal_id = terminal_id
        if db_path is None:
            db_path = os.getenv("POS_QA_TERMINAL_DB") or str(
                DEFAULT_DB_DIR / f"terminal_{terminal_id}.db"
            )
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.online = True
        self._init_db()

    # ------------------------------------------------------------------ state
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS offline_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def go_offline(self) -> dict[str, Any]:
        self.online = False
        return {"online": False, "terminal_id": self.terminal_id}

    def go_online(self) -> dict[str, Any]:
        self.online = True
        return {"online": True, "terminal_id": self.terminal_id}

    def restart(self) -> dict[str, Any]:
        """Simulates an app/terminal restart; the queue survives in SQLite."""
        self.online = True
        return {
            "online": True,
            "terminal_id": self.terminal_id,
            "queue_size": self.queue_size(),
        }

    # ----------------------------------------------------------------- actions
    def _payload(
        self,
        amount: str | float | Decimal,
        method: str,
        installments: int,
        entry_mode: str,
        card_token: str,
        capture: bool,
    ) -> dict[str, Any]:
        return {
            "amount": _money(amount),
            "currency": "BRL",
            "method": method,
            "installments": int(installments),
            "entry_mode": entry_mode,
            "terminal_id": self.terminal_id,
            "merchant_id": "MERCH0001",
            "card_token": card_token,
            "capture": bool(capture),
        }

    def _post_payment(
        self, payload: dict[str, Any], idempotency_key: str, correlation_id: str | None = None
    ) -> dict[str, Any]:
        headers = {
            "Idempotency-Key": idempotency_key,
            "X-Correlation-Id": correlation_id or str(uuid4()),
        }
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/payments",
                json=payload,
                headers=headers,
                timeout=15,
            )
        except requests.RequestException as exc:
            return {
                "status_code": 0,
                "idempotency_key": idempotency_key,
                "error": str(exc),
            }
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}
        return {
            "status_code": response.status_code,
            "idempotency_key": idempotency_key,
            "body": body,
            "correlation_id": response.headers.get("X-Correlation-Id"),
        }

    def start_sale(
        self,
        amount: str | float | Decimal,
        method: str = "credit",
        installments: int = 1,
        entry_mode: str = "chip",
        card_token: str = "tok_approved",
        capture: bool = True,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        key = idempotency_key or str(uuid4())
        payload = self._payload(
            amount, method, installments, entry_mode, card_token, capture
        )
        if not self.online:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO offline_queue "
                    "(idempotency_key, payload, created_at) VALUES (?, ?, ?)",
                    (key, json.dumps(payload, sort_keys=True), _now()),
                )
            return {
                "status": "QUEUED_OFFLINE",
                "idempotency_key": key,
                "amount": payload["amount"],
                "terminal_id": self.terminal_id,
            }
        return self._post_payment(payload, key, correlation_id)

    def queue_size(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS total FROM offline_queue").fetchone()
            return int(row["total"])

    def queued_transactions(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT idempotency_key, payload, created_at FROM offline_queue ORDER BY id"
            ).fetchall()
        return [
            {
                "idempotency_key": row["idempotency_key"],
                "payload": json.loads(row["payload"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def sync(self) -> dict[str, Any]:
        results = []
        for item in self.queued_transactions():
            result = self._post_payment(item["payload"], item["idempotency_key"])
            results.append(result)
            # 2xx, 503 and 504 are persisted by the API; retrying the same key is
            # idempotent, so the queue can be cleared. 4xx/network errors remain.
            if result["status_code"] in (200, 201, 503, 504):
                with self._connect() as conn:
                    conn.execute(
                        "DELETE FROM offline_queue WHERE idempotency_key = ?",
                        (item["idempotency_key"],),
                    )
        return {
            "terminal_id": self.terminal_id,
            "synced": len(results),
            "queue_size": self.queue_size(),
            "results": results,
        }

    def get_payment(self, payment_id: str) -> dict[str, Any]:
        response = requests.get(
            f"{self.api_url}/api/v1/payments/{payment_id}", timeout=15
        )
        return {"status_code": response.status_code, "body": response.json()}
