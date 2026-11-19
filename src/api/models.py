"""Pydantic contracts for the simulated payment API."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class PaymentRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    method: Literal["credit", "debit"] = "credit"
    installments: int = Field(default=1, ge=1, le=12)
    entry_mode: Literal["chip", "contactless", "manual"] = "chip"
    terminal_id: str = Field(min_length=1, max_length=32)
    merchant_id: str = Field(min_length=1, max_length=32)
    card_token: str = Field(default="tok_approved", min_length=1, max_length=64)
    capture: bool = True
    simulate_delay_ms: int = Field(default=0, ge=0, le=5000)


class CaptureRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)


class RefundRequest(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)


class SyncTransaction(PaymentRequest):
    idempotency_key: str = Field(min_length=8, max_length=128)


class SyncRequest(BaseModel):
    transactions: list[SyncTransaction] = Field(min_length=1, max_length=50)
