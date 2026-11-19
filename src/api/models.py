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


class InstallmentPlanItem(BaseModel):
    number: int
    amount: str


class PaymentResponse(BaseModel):
    payment_id: str
    status: str
    response_code: str
    amount: str
    captured_amount: str
    refunded_amount: str
    currency: str
    method: str
    installments: int
    installment_plan: list[InstallmentPlanItem]
    entry_mode: str
    terminal_id: str
    merchant_id: str
    capture_requested: bool
    settlement_id: str | None = None
    settled_at: str | None = None
    correlation_id: str
    created_at: str
    updated_at: str


class SettlementItem(BaseModel):
    payment_id: str
    gross_amount: str
    refunded_amount: str
    net_amount: str


class SettlementResponse(BaseModel):
    settlement_id: str
    terminal_id: str
    status: str
    transaction_count: int
    gross_amount: str
    refunded_amount: str
    net_amount: str
    correlation_id: str
    created_at: str
    items: list[SettlementItem]


class ErrorDetail(BaseModel):
    code: str
    message: str
    correlation_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail

