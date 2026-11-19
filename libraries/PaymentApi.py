"""Robot library: HTTP client for the simulated payment API."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class PaymentApi:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, **kwargs):
        response = requests.request(
            method,
            f"{self.base_url}{path}",
            timeout=20,
            **kwargs,
        )
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}
        return {
            "status_code": response.status_code,
            "body": body,
            "correlation_id": response.headers.get("X-Correlation-Id"),
        }

    def health(self):
        return self._request("GET", "/health")

    def create_payment(
        self,
        amount,
        idempotency_key=None,
        currency: str = "BRL",
        method: str = "credit",
        installments: int = 1,
        entry_mode: str = "chip",
        terminal_id: str = "TERM0001",
        merchant_id: str = "MERCH0001",
        card_token: str = "tok_approved",
        capture: bool = True,
        correlation_id=None,
    ):
        key = idempotency_key or str(uuid4())
        headers = {"Idempotency-Key": key}
        if correlation_id:
            headers["X-Correlation-Id"] = correlation_id
        payload = {
            "amount": str(amount),
            "currency": currency,
            "method": method,
            "installments": int(installments),
            "entry_mode": entry_mode,
            "terminal_id": terminal_id,
            "merchant_id": merchant_id,
            "card_token": card_token,
            "capture": bool(capture),
        }
        result = self._request("POST", "/api/v1/payments", json=payload, headers=headers)
        result["idempotency_key"] = key
        return result

    def get_payment(self, payment_id: str):
        return self._request("GET", f"/api/v1/payments/{payment_id}")

    def create_payment_without_key(self, payload: dict):
        """Negative contract helper: sends a payment without Idempotency-Key."""
        return self._request("POST", "/api/v1/payments", json=payload)

    def cancel_payment(self, payment_id: str):
        return self._request("POST", f"/api/v1/payments/{payment_id}/cancel")

    def refund_payment(self, payment_id: str, amount=None):
        payload = {} if amount is None else {"amount": str(amount)}
        return self._request(
            "POST", f"/api/v1/payments/{payment_id}/refund", json=payload
        )

    def sync_terminal(self, terminal_id: str, transactions: list[dict]):
        return self._request(
            "POST",
            f"/api/v1/terminals/{terminal_id}/sync",
            json={"transactions": transactions},
        )
