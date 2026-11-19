from __future__ import annotations

from copy import deepcopy

from jsonschema import Draft202012Validator

from src.api.main import app


def schema(name: str) -> dict:
    document = app.openapi()
    component = deepcopy(document["components"]["schemas"][name])
    # FastAPI emits local refs like #/components/schemas/...; keep the root
    # components available so the validator can resolve them.
    component["components"] = document["components"]
    return component


def assert_valid(instance: dict, name: str) -> None:
    errors = sorted(Draft202012Validator(schema(name)).iter_errors(instance), key=str)
    assert not errors, "\n".join(error.message for error in errors)


def create(client, key: str, amount: str = "10.00", capture: bool = True):
    return client.post(
        "/api/v1/payments",
        json={
            "amount": amount,
            "terminal_id": "TERM-CONTRACT-01",
            "merchant_id": "MERCH0001",
            "capture": capture,
        },
        headers={"Idempotency-Key": key},
    )


def test_payment_response_matches_openapi_schema(client):
    response = create(client, "contract-payment-001")
    assert response.status_code == 201
    assert_valid(response.json(), "PaymentResponse")


def test_capture_response_matches_openapi_schema(client):
    created = create(client, "contract-capture-001", capture=False).json()
    response = client.post(f"/api/v1/payments/{created['payment_id']}/capture", json={})
    assert response.status_code == 200
    assert_valid(response.json(), "PaymentResponse")


def test_settlement_response_matches_openapi_schema(client):
    create(client, "contract-set-001", amount="15.00")
    response = client.post(
        "/api/v1/terminals/TERM-CONTRACT-01/settlement",
        headers={"Idempotency-Key": "contract-set-key-001"},
    )
    assert response.status_code == 201
    assert_valid(response.json(), "SettlementResponse")


def test_error_response_matches_openapi_schema(client):
    created = create(client, "contract-error-001").json()
    response = client.post(f"/api/v1/payments/{created['payment_id']}/cancel")
    assert response.status_code == 409
    assert_valid(response.json(), "ErrorResponse")
