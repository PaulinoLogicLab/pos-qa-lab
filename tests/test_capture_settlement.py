from __future__ import annotations

from fastapi.testclient import TestClient


def create(
    client: TestClient,
    key: str,
    amount: str = "100.00",
    capture: bool = True,
    terminal_id: str = "TERM-CAP-01",
    card_token: str = "tok_approved",
):
    return client.post(
        "/api/v1/payments",
        json={
            "amount": amount,
            "currency": "BRL",
            "method": "credit",
            "installments": 1,
            "entry_mode": "chip",
            "terminal_id": terminal_id,
            "merchant_id": "MERCH0001",
            "card_token": card_token,
            "capture": capture,
        },
        headers={"Idempotency-Key": key},
    )


def test_full_capture(client):
    created = create(client, "cap-full-001", capture=False).json()
    assert created["status"] == "AUTHORIZED"
    response = client.post(f"/api/v1/payments/{created['payment_id']}/capture", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CAPTURED"
    assert body["captured_amount"] == "100.00"
    assert body["refunded_amount"] == "0.00"


def test_partial_capture_then_refund(client):
    created = create(client, "cap-partial-001", capture=False).json()
    payment_id = created["payment_id"]
    captured = client.post(
        f"/api/v1/payments/{payment_id}/capture", json={"amount": "40.00"}
    )
    assert captured.status_code == 200
    assert captured.json()["status"] == "PARTIALLY_CAPTURED"
    assert captured.json()["captured_amount"] == "40.00"

    refund = client.post(f"/api/v1/payments/{payment_id}/refund", json={"amount": "40.00"})
    assert refund.status_code == 200
    assert refund.json()["status"] == "REFUNDED"
    assert refund.json()["refunded_amount"] == "40.00"

    too_much = client.post(
        f"/api/v1/payments/{payment_id}/refund", json={"amount": "10.00"}
    )
    assert too_much.status_code == 409


def test_capture_after_cancel_is_rejected(client):
    created = create(client, "cap-cancel-001", capture=False).json()
    client.post(f"/api/v1/payments/{created['payment_id']}/cancel")
    response = client.post(f"/api/v1/payments/{created['payment_id']}/capture", json={})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_TRANSITION"


def test_capture_is_idempotent_for_same_amount(client):
    created = create(client, "cap-idem-001", capture=False).json()
    first = client.post(f"/api/v1/payments/{created['payment_id']}/capture", json={})
    second = client.post(f"/api/v1/payments/{created['payment_id']}/capture", json={})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == second.json()["status"] == "CAPTURED"

    different = client.post(
        f"/api/v1/payments/{created['payment_id']}/capture", json={"amount": "10.00"}
    )
    assert different.status_code == 409


def test_settlement_totals_idempotency_and_empty_batch(client):
    terminal = "TERM-SET-001"
    first = create(client, "set-pay-001", amount="100.00", terminal_id=terminal).json()
    second = create(client, "set-pay-002", amount="50.00", terminal_id=terminal).json()
    refund = client.post(
        f"/api/v1/payments/{second['payment_id']}/refund", json={"amount": "20.00"}
    )
    assert refund.status_code == 200

    response = client.post(
        f"/api/v1/terminals/{terminal}/settlement",
        headers={"Idempotency-Key": "set-key-001"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "SETTLED"
    assert body["transaction_count"] == 2
    assert body["gross_amount"] == "150.00"
    assert body["refunded_amount"] == "20.00"
    assert body["net_amount"] == "130.00"
    assert {item["payment_id"] for item in body["items"]} == {
        first["payment_id"],
        second["payment_id"],
    }

    replay = client.post(
        f"/api/v1/terminals/{terminal}/settlement",
        headers={"Idempotency-Key": "set-key-001"},
    )
    assert replay.status_code == 201
    assert replay.json()["settlement_id"] == body["settlement_id"]

    empty = client.post(
        f"/api/v1/terminals/{terminal}/settlement",
        headers={"Idempotency-Key": "set-key-002"},
    )
    assert empty.status_code == 201
    assert empty.json()["status"] == "EMPTY"
    assert empty.json()["transaction_count"] == 0
    assert empty.json()["net_amount"] == "0.00"

    fetched = client.get(f"/api/v1/settlements/{body['settlement_id']}")
    assert fetched.status_code == 200
    assert fetched.json()["net_amount"] == "130.00"


def test_settlement_key_cannot_be_reused_for_another_terminal(client):
    create(client, "set-cross-001", terminal_id="TERM-SET-A")
    first = client.post(
        "/api/v1/terminals/TERM-SET-A/settlement",
        headers={"Idempotency-Key": "set-cross-key"},
    )
    assert first.status_code == 201
    second = client.post(
        "/api/v1/terminals/TERM-SET-B/settlement",
        headers={"Idempotency-Key": "set-cross-key"},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
