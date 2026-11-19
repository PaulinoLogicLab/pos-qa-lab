"""FastAPI entry point for the simulated payment acquirer."""

from __future__ import annotations

import json
import logging
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, Header, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .db import init_db
from .models import (
    CaptureRequest,
    ErrorResponse,
    PaymentRequest,
    PaymentResponse,
    RefundRequest,
    SettlementResponse,
    SyncRequest,
)
from .service import (
    ServiceError,
    cancel_payment,
    capture_payment,
    create_payment,
    get_payment,
    get_settlement,
    refund_payment,
    settle_terminal,
    sync_transactions,
)

logger = logging.getLogger("pos_qa")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

app = FastAPI(
    title="POS QA Lab - Simulated Payment API",
    version="1.0.0",
    description=(
        "API de laboratorio para jornadas de pagamento. Nao e um adquirente real, "
        "nao implementa EMV, ISO 8583 de producao ou PCI PTS."
    ),
)

init_db()


def log_event(event: str, **fields: object) -> None:
    logger.info(json.dumps({"event": event, **fields}, ensure_ascii=False, default=str))


def correlation(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


def error_response(exc: ServiceError, cid: str) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "correlation_id": cid,
            }
        },
    )


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    cid = request.headers.get("X-Correlation-Id") or str(uuid4())
    request.state.correlation_id = cid
    response = await call_next(request)
    response.headers["X-Correlation-Id"] = cid
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    cid = correlation(request)
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "request validation failed",
                "details": jsonable_encoder(exc.errors()),
                "correlation_id": cid,
            }
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/v1/payments",
    responses={
        201: {"model": PaymentResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
def create(
    payload: PaymentRequest,
    request: Request,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=128)
    ],
):
    cid = correlation(request)
    try:
        body, status_code = create_payment(payload, idempotency_key, cid)
    except ServiceError as exc:
        log_event("payment_rejected", correlation_id=cid, code=exc.code, status=exc.status_code)
        return error_response(exc, cid)
    log_event(
        "payment_created",
        correlation_id=cid,
        payment_id=body["payment_id"],
        status=body["status"],
        response_code=body["response_code"],
        amount=body["amount"],
        terminal_id=body["terminal_id"],
    )
    return JSONResponse(status_code=status_code, content=body)


@app.get("/api/v1/payments/{payment_id}", response_model=PaymentResponse)
def read(payment_id: str, request: Request):
    cid = correlation(request)
    try:
        return get_payment(payment_id)
    except ServiceError as exc:
        return error_response(exc, cid)


@app.post("/api/v1/payments/{payment_id}/cancel", response_model=PaymentResponse)
def cancel(payment_id: str, request: Request):
    cid = correlation(request)
    try:
        body = cancel_payment(payment_id, cid)
    except ServiceError as exc:
        log_event("cancel_rejected", correlation_id=cid, payment_id=payment_id, code=exc.code)
        return error_response(exc, cid)
    log_event("payment_cancelled", correlation_id=cid, payment_id=payment_id, status=body["status"])
    return body


@app.post("/api/v1/payments/{payment_id}/refund", response_model=PaymentResponse)
def refund(payment_id: str, request: Request, payload: RefundRequest | None = None):
    cid = correlation(request)
    try:
        body = refund_payment(payment_id, payload or RefundRequest(), cid)
    except ServiceError as exc:
        log_event("refund_rejected", correlation_id=cid, payment_id=payment_id, code=exc.code)
        return error_response(exc, cid)
    log_event(
        "payment_refunded",
        correlation_id=cid,
        payment_id=payment_id,
        status=body["status"],
        refunded_amount=body["refunded_amount"],
    )
    return body


@app.post("/api/v1/payments/{payment_id}/capture", response_model=PaymentResponse)
def capture(payment_id: str, request: Request, payload: CaptureRequest | None = None):
    cid = correlation(request)
    try:
        body = capture_payment(payment_id, payload or CaptureRequest(), cid)
    except ServiceError as exc:
        log_event("capture_rejected", correlation_id=cid, payment_id=payment_id, code=exc.code)
        return error_response(exc, cid)
    log_event(
        "payment_captured",
        correlation_id=cid,
        payment_id=payment_id,
        status=body["status"],
        captured_amount=body["captured_amount"],
    )
    return body


@app.post(
    "/api/v1/terminals/{terminal_id}/settlement",
    response_model=SettlementResponse,
    responses={409: {"model": ErrorResponse}},
)
def settlement(
    terminal_id: str,
    request: Request,
    idempotency_key: Annotated[
        str, Header(alias="Idempotency-Key", min_length=8, max_length=128)
    ],
):
    cid = correlation(request)
    try:
        body = settle_terminal(terminal_id, cid, idempotency_key)
    except ServiceError as exc:
        log_event("settlement_rejected", correlation_id=cid, terminal_id=terminal_id, code=exc.code)
        return error_response(exc, cid)
    log_event(
        "terminal_settled",
        correlation_id=cid,
        terminal_id=terminal_id,
        settlement_id=body["settlement_id"],
        status=body["status"],
        net_amount=body["net_amount"],
    )
    return JSONResponse(status_code=201, content=body)


@app.get("/api/v1/settlements/{settlement_id}", response_model=SettlementResponse)
def read_settlement(settlement_id: str, request: Request):
    cid = correlation(request)
    try:
        return get_settlement(settlement_id)
    except ServiceError as exc:
        return error_response(exc, cid)


@app.post("/api/v1/terminals/{terminal_id}/sync")
def sync(terminal_id: str, payload: SyncRequest, request: Request):
    cid = correlation(request)
    results = sync_transactions(payload, cid, terminal_id=terminal_id)
    log_event(
        "terminal_synced",
        correlation_id=cid,
        terminal_id=terminal_id,
        transactions=len(results),
        approved=sum(1 for item in results if item.get("body", {}).get("status") == "CAPTURED"),
    )
    return {"terminal_id": terminal_id, "results": results}
