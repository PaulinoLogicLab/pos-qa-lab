"""Business rules for the simulated payment API.

The service models the journeys named in the job description (sale, cancel,
refund, installments, timeout, duplicate request) without pretending to be a
real acquirer or an EMV/PCI implementation.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import uuid4

from .db import connect, utc_now
from .models import PaymentRequest, RefundRequest, SyncRequest

APPROVED = "00"
DECLINED = "05"
INVALID_TRANSACTION = "12"
TIMEOUT = "91"
SYSTEM_ERROR = "96"


class ServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def to_cents(amount: Decimal) -> int:
    cents = int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))
    if Decimal(cents) / 100 != amount:
        raise ServiceError(422, "INVALID_AMOUNT", "amount must have at most two decimals")
    return cents


def cents_to_str(cents: int) -> str:
    return f"{Decimal(cents) / 100:.2f}"


def installment_plan(amount_cents: int, installments: int) -> list[dict[str, Any]]:
    base = amount_cents // installments
    remainder = amount_cents % installments
    plan = []
    for index in range(installments):
        value = base + (1 if index < remainder else 0)
        plan.append({"number": index + 1, "amount": cents_to_str(value)})
    return plan


def request_hash(payload: PaymentRequest) -> str:
    canonical = json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize(row: sqlite3.Row) -> dict[str, Any]:
    amount_cents = int(row["amount_cents"])
    return {
        "payment_id": row["id"],
        "status": row["status"],
        "response_code": row["response_code"],
        "amount": cents_to_str(amount_cents),
        "currency": row["currency"],
        "method": row["method"],
        "installments": int(row["installments"]),
        "installment_plan": installment_plan(amount_cents, int(row["installments"])),
        "entry_mode": row["entry_mode"],
        "terminal_id": row["terminal_id"],
        "merchant_id": row["merchant_id"],
        "capture_requested": bool(row["capture_requested"]),
        "refunded_amount": cents_to_str(int(row["refunded_cents"])),
        "correlation_id": row["correlation_id"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _event(
    conn: sqlite3.Connection,
    payment_id: str,
    event_type: str,
    from_status: str | None,
    to_status: str | None,
    amount_cents: int | None,
    correlation_id: str,
) -> None:
    conn.execute(
        """
        INSERT INTO payment_events
            (payment_id, event_type, from_status, to_status, amount_cents,
             correlation_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (payment_id, event_type, from_status, to_status, amount_cents, correlation_id, utc_now()),
    )


def _outcome(card_token: str, capture_requested: bool) -> tuple[str, str, int]:
    if card_token == "tok_declined":
        return "DECLINED", DECLINED, 201
    if card_token == "tok_timeout":
        return "FAILED", TIMEOUT, 504
    if card_token == "tok_error":
        return "FAILED", SYSTEM_ERROR, 503
    if capture_requested:
        return "CAPTURED", APPROVED, 201
    return "AUTHORIZED", APPROVED, 201


def create_payment(
    payload: PaymentRequest,
    idempotency_key: str,
    correlation_id: str,
    db_file: str | None = None,
) -> tuple[dict[str, Any], int]:
    if payload.currency.upper() != "BRL":
        raise ServiceError(422, "UNSUPPORTED_CURRENCY", "only BRL is supported in this lab")

    payload_hash = request_hash(payload)
    with connect(db_file) as conn:
        existing = conn.execute(
            "SELECT * FROM payments WHERE idempotency_key = ?", (idempotency_key,)
        ).fetchone()
        if existing:
            if existing["request_hash"] != payload_hash:
                raise ServiceError(
                    409,
                    "IDEMPOTENCY_CONFLICT",
                    "the same Idempotency-Key was used with a different payload",
                )
            return serialize(existing), int(existing["http_status"])

        amount_cents = to_cents(payload.amount)
        status, response_code, http_status = _outcome(payload.card_token, payload.capture)
        payment_id = str(uuid4())
        now = utc_now()
        conn.execute(
            """
            INSERT INTO payments (
                id, idempotency_key, request_hash, amount_cents, currency, method, installments,
                entry_mode, terminal_id, merchant_id, card_token, capture_requested, status,
                response_code, http_status, refunded_cents, correlation_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (
                payment_id,
                idempotency_key,
                payload_hash,
                amount_cents,
                payload.currency.upper(),
                payload.method,
                payload.installments,
                payload.entry_mode,
                payload.terminal_id,
                payload.merchant_id,
                payload.card_token,
                int(payload.capture),
                status,
                response_code,
                http_status,
                correlation_id,
                now,
                now,
            ),
        )
        _event(conn, payment_id, "PAYMENT_CREATED", None, status, amount_cents, correlation_id)
        row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
        return serialize(row), http_status


def get_payment(payment_id: str, db_file: str | None = None) -> dict[str, Any]:
    with connect(db_file) as conn:
        row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
        if not row:
            raise ServiceError(404, "PAYMENT_NOT_FOUND", "payment not found")
        return serialize(row)


def cancel_payment(
    payment_id: str, correlation_id: str, db_file: str | None = None
) -> dict[str, Any]:
    with connect(db_file) as conn:
        row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
        if not row:
            raise ServiceError(404, "PAYMENT_NOT_FOUND", "payment not found")
        if row["status"] == "CANCELLED":
            return serialize(row)
        if row["status"] != "AUTHORIZED":
            raise ServiceError(
                409,
                "INVALID_TRANSITION",
                f"cancel is not allowed from status {row['status']}",
            )
        now = utc_now()
        conn.execute(
            "UPDATE payments SET status = ?, response_code = ?, updated_at = ? WHERE id = ?",
            ("CANCELLED", APPROVED, now, payment_id),
        )
        _event(
            conn,
            payment_id,
            "PAYMENT_CANCELLED",
            row["status"],
            "CANCELLED",
            int(row["amount_cents"]),
            correlation_id,
        )
        updated = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
        return serialize(updated)


def refund_payment(
    payment_id: str,
    payload: RefundRequest,
    correlation_id: str,
    db_file: str | None = None,
) -> dict[str, Any]:
    with connect(db_file) as conn:
        row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
        if not row:
            raise ServiceError(404, "PAYMENT_NOT_FOUND", "payment not found")
        if row["status"] not in ("CAPTURED", "PARTIALLY_REFUNDED"):
            raise ServiceError(
                409,
                "INVALID_TRANSITION",
                f"refund is not allowed from status {row['status']}",
            )
        amount_cents = int(row["amount_cents"])
        refunded_cents = int(row["refunded_cents"])
        remaining = amount_cents - refunded_cents
        if payload.amount is None:
            refund_cents = remaining
        else:
            refund_cents = to_cents(payload.amount)
            if refund_cents <= 0 or refund_cents > remaining:
                raise ServiceError(
                    422,
                    "INVALID_REFUND_AMOUNT",
                    f"refund must be between 0.01 and {cents_to_str(remaining)}",
                )
        new_refunded = refunded_cents + refund_cents
        new_status = "REFUNDED" if new_refunded == amount_cents else "PARTIALLY_REFUNDED"
        now = utc_now()
        conn.execute(
            """
            UPDATE payments
               SET status = ?, response_code = ?, refunded_cents = ?, updated_at = ?
             WHERE id = ?
            """,
            (new_status, APPROVED, new_refunded, now, payment_id),
        )
        conn.execute(
            "INSERT INTO refunds (id, payment_id, amount_cents, correlation_id, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(uuid4()), payment_id, refund_cents, correlation_id, now),
        )
        _event(
            conn,
            payment_id,
            "PAYMENT_REFUNDED",
            row["status"],
            new_status,
            refund_cents,
            correlation_id,
        )
        updated = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
        return serialize(updated)


def sync_transactions(
    payload: SyncRequest,
    correlation_id: str,
    db_file: str | None = None,
    terminal_id: str | None = None,
) -> list[dict[str, Any]]:
    results = []
    for transaction in payload.transactions:
        if terminal_id and transaction.terminal_id != terminal_id:
            results.append(
                {
                    "idempotency_key": transaction.idempotency_key,
                    "status_code": 422,
                    "error": {
                        "code": "TERMINAL_MISMATCH",
                        "message": (
                            f"transaction terminal {transaction.terminal_id} does not match "
                            f"path terminal {terminal_id}"
                        ),
                    },
                }
            )
            continue
        try:
            body, status = create_payment(
                transaction, transaction.idempotency_key, correlation_id, db_file
            )
            results.append(
                {
                    "idempotency_key": transaction.idempotency_key,
                    "status_code": status,
                    "body": body,
                }
            )
        except ServiceError as exc:
            results.append(
                {
                    "idempotency_key": transaction.idempotency_key,
                    "status_code": exc.status_code,
                    "error": {"code": exc.code, "message": exc.message},
                }
            )
    return results
