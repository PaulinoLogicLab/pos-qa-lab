from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from src.api.db import connect, init_db
from src.api.models import PaymentRequest
from src.api.service import create_payment


def payload(amount: str = "10.00") -> PaymentRequest:
    return PaymentRequest(
        amount=amount,
        terminal_id="TERM-CONC-01",
        merchant_id="MERCH0001",
    )


def test_same_idempotency_key_ten_times_creates_one_payment(tmp_path, monkeypatch):
    db_file = tmp_path / "concurrency.db"
    monkeypatch.setenv("POS_QA_DB", str(db_file))
    init_db()
    request = payload()
    barrier = threading.Barrier(10)

    def call(index: int) -> str:
        barrier.wait(timeout=10)
        result, _status = create_payment(request, "concurrent-key-001", f"corr-{index}")
        return result["payment_id"]

    with ThreadPoolExecutor(max_workers=10) as pool:
        ids = list(pool.map(call, range(10)))

    assert len(set(ids)) == 1
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM payments WHERE idempotency_key = ?",
            ("concurrent-key-001",),
        ).fetchone()
        assert int(row["total"]) == 1


def test_delayed_request_retry_does_not_duplicate(tmp_path, monkeypatch):
    db_file = tmp_path / "delay.db"
    monkeypatch.setenv("POS_QA_DB", str(db_file))
    init_db()
    request = payload("25.00").model_copy(update={"simulate_delay_ms": 400})

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(create_payment, request, "delay-key-001", "corr-1")
        time.sleep(0.05)
        second = pool.submit(create_payment, request, "delay-key-001", "corr-2")
        first_result, _ = first.result(timeout=10)
        second_result, _ = second.result(timeout=10)

    assert first_result["payment_id"] == second_result["payment_id"]
    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM payments WHERE idempotency_key = ?",
            ("delay-key-001",),
        ).fetchone()
        assert int(row["total"]) == 1
