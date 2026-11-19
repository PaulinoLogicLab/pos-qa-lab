"""Peripheral and terminal-lifecycle simulators.

These are deterministic lab models, not hardware drivers. They exist to test
the behaviour around printer failures, pinpad outcomes, reboot and firmware
update without claiming real POS integration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

PRINTER_STATUSES = {"OK", "PAPER_OUT", "OFFLINE"}
PINPAD_MODES = {"OK", "TIMEOUT", "CANCELLED"}
PINPAD_STATUSES = {"CONNECTED", "DISCONNECTED"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Printer:
    def __init__(self) -> None:
        self.status = "OK"
        self.pending: list[dict[str, Any]] = []
        self.printed: list[dict[str, Any]] = []

    def set_status(self, status: str) -> dict[str, Any]:
        if status not in PRINTER_STATUSES:
            raise ValueError(f"invalid printer status: {status}")
        self.status = status
        return {"status": self.status}

    def print_receipt(self, receipt: dict[str, Any]) -> dict[str, Any]:
        item = dict(receipt)
        item.setdefault("receipt_id", str(uuid4()))
        item["created_at"] = _now()
        if self.status == "OK":
            self.printed.append(item)
            return {"status": "PRINTED", "receipt_id": item["receipt_id"]}
        self.pending.append(item)
        return {"status": self.status, "receipt_id": item["receipt_id"]}

    def refill(self) -> dict[str, Any]:
        self.status = "OK"
        return {"status": self.status, "pending": len(self.pending)}

    def reconnect(self) -> dict[str, Any]:
        self.status = "OK"
        return {"status": self.status, "pending": len(self.pending)}

    def reprint_pending(self) -> dict[str, Any]:
        if self.status != "OK":
            return {"status": self.status, "reprinted": 0, "pending": len(self.pending)}
        reprinted = 0
        for item in self.pending:
            self.printed.append(item)
            reprinted += 1
        self.pending.clear()
        return {"status": "PRINTED", "reprinted": reprinted, "pending": 0}

    def pending_count(self) -> int:
        return len(self.pending)

    def printed_count(self) -> int:
        return len(self.printed)


class Pinpad:
    def __init__(self) -> None:
        self.status = "CONNECTED"
        self.mode = "OK"

    def configure(self, mode: str | None = None, status: str | None = None) -> dict[str, Any]:
        if mode is not None:
            if mode not in PINPAD_MODES:
                raise ValueError(f"invalid pinpad mode: {mode}")
            self.mode = mode
        if status is not None:
            if status not in PINPAD_STATUSES:
                raise ValueError(f"invalid pinpad status: {status}")
            self.status = status
        return {"status": self.status, "mode": self.mode}

    def request_pin(self, amount: str) -> dict[str, Any]:
        if self.status == "DISCONNECTED":
            return {"status": "DISCONNECTED", "amount": amount}
        if self.mode == "TIMEOUT":
            return {"status": "TIMEOUT", "amount": amount}
        if self.mode == "CANCELLED":
            return {"status": "CANCELLED", "amount": amount}
        return {"status": "APPROVED", "amount": amount}


class TerminalLifecycle:
    def __init__(self) -> None:
        self.firmware_version = "1.0.0"
        self.config: dict[str, Any] = {"display_language": "pt-BR"}
        self.boot_count = 0

    def reboot(self) -> dict[str, Any]:
        self.boot_count += 1
        return {"boot_count": self.boot_count, "firmware_version": self.firmware_version}

    def update_firmware(self, version: str) -> dict[str, Any]:
        if not version.strip():
            raise ValueError("firmware version is required")
        self.firmware_version = version
        return {"firmware_version": self.firmware_version}

    def update_config(self, key: str, value: str) -> dict[str, Any]:
        if not key.strip():
            raise ValueError("config key is required")
        self.config[key] = value
        return {"key": key, "value": value, "config": dict(self.config)}
