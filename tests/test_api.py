from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.api.db import init_db
from src.api.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "api.db"
    monkeypatch.setenv("POS_QA_DB", str(db_file))
    init_db()
    with TestClient(app) as test_client:
        yield test_client


def create(client: TestClient, key: str, **overrides):
    payload = {
        "amount": "125.90",
        "currency": "BRL",
        "method": "credit",
        "installments": 1,
        "entry_mode": "chip",
        "terminal_id": "TERM0001",
        "merchant_id": "MERCH0001",
        "card_token": "tok_approved",
        "capture": True,
    }
    payload.update(overrides)
    return client.post(
        "/api/v1/payments",
        json=payload,
        headers={"Idempotency-Key": key},
    )


def count(key: str) -> int:
    from src.api.db import connect

    with connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM payments WHERE idempotency_key = ?", (key,)
        ).fetchone()
        return int(row["total"])


def test_approved_sale(client):
    response = create(client, "idem-approved-001")
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "CAPTURED"
    assert body["response_code"] == "00"
    assert body["amount"] == "125.90"
    assert body["installment_plan"] == [{"number": 1, "amount": "125.90"}]
    assert count("idem-approved-001") == 1


def test_declined_sale(client):
    response = create(client, "idem-declined-001", card_token="tok_declined")
    assert response.status_code == 201
    assert response.json()["status"] == "DECLINED"
    assert response.json()["response_code"] == "05"


def test_idempotent_replay_returns_same_payment(client):
    first = create(client, "idem-replay-001")
    second = create(client, "idem-replay-001")
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["payment_id"] == second.json()["payment_id"]
    assert count("idem-replay-001") == 1


def test_idempotency_conflict_with_different_payload(client):
    first = create(client, "idem-conflict-001")
    second = create(client, "idem-conflict-001", amount="10.00")
    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_cancel_authorized_payment(client):
    created = create(client, "idem-cancel-001", capture=False).json()
    response = client.post(f"/api/v1/payments/{created['payment_id']}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_cancel_captured_payment_is_invalid(client):
    created = create(client, "idem-cancel-002").json()
    response = client.post(f"/api/v1/payments/{created['payment_id']}/cancel")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_TRANSITION"


def test_partial_and_full_refund(client):
    created = create(client, "idem-refund-001").json()
    payment_id = created["payment_id"]

    partial = client.post(
        f"/api/v1/payments/{payment_id}/refund", json={"amount": "50.00"}
    )
    assert partial.status_code == 200
    assert partial.json()["status"] == "PARTIALLY_REFUNDED"
    assert partial.json()["refunded_amount"] == "50.00"

    full = client.post(f"/api/v1/payments/{payment_id}/refund")
    assert full.status_code == 200
    assert full.json()["status"] == "REFUNDED"
    assert full.json()["refunded_amount"] == "125.90"


def test_refund_before_capture_is_invalid(client):
    created = create(client, "idem-refund-002", capture=False).json()
    response = client.post(f"/api/v1/payments/{created['payment_id']}/refund")
    assert response.status_code == 409


def test_refund_above_remaining_is_rejected(client):
    created = create(client, "idem-refund-003").json()
    response = client.post(
        f"/api/v1/payments/{created['payment_id']}/refund", json={"amount": "999.00"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REFUND_AMOUNT"


def test_installments_rounding(client):
    response = create(client, "idem-installments-001", amount="100.00", installments=3)
    plan = response.json()["installment_plan"]
    assert [item["amount"] for item in plan] == ["33.34", "33.33", "33.33"]


def test_contract_rejects_invalid_payloads(client):
    assert create(client, "idem-invalid-001", amount="-1.00").status_code == 422
    assert create(client, "idem-invalid-002", currency="USD").status_code == 422
    assert create(client, "idem-invalid-003", installments=0).status_code == 422
    response = client.post(
        "/api/v1/payments",
        json={"amount": "10.00", "terminal_id": "T", "merchant_id": "M"},
    )
    assert response.status_code == 422


def test_timeout_is_persisted_and_retry_is_idempotent(client):
    first = create(client, "idem-timeout-001", card_token="tok_timeout")
    second = create(client, "idem-timeout-001", card_token="tok_timeout")
    assert first.status_code == 504
    assert first.json()["status"] == "FAILED"
    assert first.json()["response_code"] == "91"
    assert second.status_code == 504
    assert second.json()["payment_id"] == first.json()["payment_id"]
    assert count("idem-timeout-001") == 1


def test_correlation_id_is_returned_and_persisted(client):
    response = client.post(
        "/api/v1/payments",
        json={
            "amount": "10.00",
            "terminal_id": "TERM0001",
            "merchant_id": "MERCH0001",
        },
        headers={
            "Idempotency-Key": "idem-correlation-001",
            "X-Correlation-Id": "corr-test-123",
        },
    )
    assert response.status_code == 201
    assert response.headers["X-Correlation-Id"] == "corr-test-123"
    payment_id = response.json()["payment_id"]
    from src.api.db import connect

    with connect() as conn:
        row = conn.execute(
            "SELECT correlation_id FROM payments WHERE id = ?", (payment_id,)
        ).fetchone()
        assert row["correlation_id"] == "corr-test-123"


def test_sync_endpoint_processes_two_transactions(client):
    response = client.post(
        "/api/v1/terminals/TERM0001/sync",
        json={
            "transactions": [
                {
                    "amount": "10.00",
                    "terminal_id": "TERM0001",
                    "merchant_id": "MERCH0001",
                    "idempotency_key": "idem-sync-001",
                },
                {
                    "amount": "20.00",
                    "terminal_id": "TERM0001",
                    "merchant_id": "MERCH0001",
                    "idempotency_key": "idem-sync-002",
                },
            ]
        },
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 2
    assert all(item["body"]["status"] == "CAPTURED" for item in results)


def test_sync_rejects_transaction_from_another_terminal(client):
    response = client.post(
        "/api/v1/terminals/TERM0001/sync",
        json={
            "transactions": [
                {
                    "amount": "10.00",
                    "terminal_id": "TERM9999",
                    "merchant_id": "MERCH0001",
                    "idempotency_key": "idem-sync-mismatch-001",
                }
            ]
        },
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["status_code"] == 422
    assert result["error"]["code"] == "TERMINAL_MISMATCH"
    assert count("idem-sync-mismatch-001") == 0
