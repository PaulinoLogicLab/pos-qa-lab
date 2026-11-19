from __future__ import annotations

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from iso8583_lab.parser import build_message, parse_message
from src.api.service import cents_to_str, installment_plan, to_cents


@settings(max_examples=100)
@given(
    amount_cents=st.integers(min_value=1, max_value=99_999_999),
    installments=st.integers(min_value=1, max_value=12),
)
def test_installment_plan_preserves_total(amount_cents: int, installments: int):
    plan = installment_plan(amount_cents, installments)
    assert len(plan) == installments
    assert sum(Decimal(item["amount"]) for item in plan) == Decimal(amount_cents) / 100
    assert all(item["amount"].count(".") == 1 for item in plan)


@settings(max_examples=100)
@given(amount_cents=st.integers(min_value=0, max_value=99_999_999))
def test_cents_round_trip(amount_cents: int):
    money = cents_to_str(amount_cents)
    assert to_cents(Decimal(money)) == amount_cents


@settings(max_examples=50)
@given(value=st.integers(min_value=0, max_value=99_999_999))
def test_iso_amount_field_round_trip(value: int):
    amount = f"{value:012d}"
    message = build_message(
        "0100",
        {
            2: "4111111111111111",
            3: "000000",
            4: amount,
            7: "1119183000",
            11: "000123",
            12: "183000",
            13: "1119",
            41: "TERM0001",
            42: "MERCH0000000001",
            49: "986",
        },
    )
    parsed = parse_message(message)
    assert parsed["fields"]["4"] == amount
