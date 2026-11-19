"""Robot library with business-level sales workflows.

The suites call these keywords; HTTP, idempotency and assertions stay in
Python, keeping the .robot files focused on the business scenario.
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "libraries"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from PaymentApi import PaymentApi  # noqa: E402


class SalesWorkflow:
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.api = PaymentApi(base_url)

    def create_sale(
        self,
        amount,
        installments: int = 1,
        card_token: str = "tok_approved",
        terminal_id: str = "TERM0001",
        capture: bool = True,
        idempotency_key: str | None = None,
        simulate_delay_ms: int = 0,
        request_timeout: float = 20,
    ):
        return self.api.create_payment(
            amount=amount,
            installments=installments,
            card_token=card_token,
            terminal_id=terminal_id,
            capture=capture,
            idempotency_key=idempotency_key or str(uuid4()),
            simulate_delay_ms=simulate_delay_ms,
            request_timeout=request_timeout,
        )

    def create_and_assert_sale(
        self,
        test_id: str,
        amount,
        installments,
        card_token,
        expected_status,
        expected_code,
        expected_plan_length,
    ):
        result = self.create_sale(
            amount=amount,
            installments=int(installments),
            card_token=card_token,
        )
        if result.get("status_code") != 201:
            raise AssertionError(
                f"{test_id}: expected HTTP 201, got {result.get('status_code')} "
                f"({result.get('body')})"
            )
        body = result["body"]
        if body.get("status") != expected_status:
            raise AssertionError(f"{test_id}: expected {expected_status}, got {body.get('status')}")
        if str(body.get("response_code")) != str(expected_code):
            raise AssertionError(
                f"{test_id}: expected code {expected_code}, got {body.get('response_code')}"
            )
        plan = body.get("installment_plan", [])
        if len(plan) != int(expected_plan_length):
            raise AssertionError(
                f"{test_id}: expected {expected_plan_length} installments, got {len(plan)}"
            )
        return result

    def create_authorized_and_capture(
        self, amount, capture_amount=None, terminal_id: str = "TERM0001"
    ):
        authorized = self.create_sale(
            amount=amount, capture=False, terminal_id=terminal_id
        )
        if authorized.get("status_code") != 201:
            raise AssertionError(f"authorization failed: {authorized}")
        payment_id = authorized["body"]["payment_id"]
        captured = self.api.capture_payment(payment_id, capture_amount)
        if captured.get("status_code") != 200:
            raise AssertionError(f"capture failed: {captured}")
        return captured

    def settle_and_assert(
        self, terminal_id: str, expected_net, expected_count, idempotency_key: str | None = None
    ):
        settlement = self.api.settle_terminal(
            terminal_id, idempotency_key or str(uuid4())
        )
        if settlement.get("status_code") != 201:
            raise AssertionError(f"settlement failed: {settlement}")
        body = settlement["body"]
        if str(body.get("net_amount")) != str(expected_net):
            raise AssertionError(
                f"expected net {expected_net}, got {body.get('net_amount')}"
            )
        if int(body.get("transaction_count")) != int(expected_count):
            raise AssertionError(
                f"expected {expected_count} transactions, got {body.get('transaction_count')}"
            )
        return settlement
