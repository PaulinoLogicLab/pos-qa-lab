"""Robot library for simulated POS peripherals and terminal lifecycle."""

from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "libraries"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from src.terminal.peripherals import Pinpad, Printer, TerminalLifecycle  # noqa: E402
from src.terminal.simulator import TerminalSimulator  # noqa: E402


def _money(value) -> str:
    return f"{Decimal(str(value)).quantize(Decimal('0.01')):.2f}"


class Hardware:
    def __init__(self, api_url: str | None = None) -> None:
        self.api_url = api_url or os.getenv("API_URL", "http://127.0.0.1:8000")
        self.terminal: TerminalSimulator | None = None
        self.printer = Printer()
        self.pinpad = Pinpad()
        self.lifecycle = TerminalLifecycle()

    def use_device(self, terminal_id: str = "TERM-HW-01", db_path: str | None = None):
        self.terminal = TerminalSimulator(self.api_url, terminal_id, db_path)
        self.printer = Printer()
        self.pinpad = Pinpad()
        self.lifecycle = TerminalLifecycle()
        return {"terminal_id": terminal_id, "db_path": str(self.terminal.db_path)}

    def _require_terminal(self) -> TerminalSimulator:
        if self.terminal is None:
            raise AssertionError("use_device must be called before this keyword")
        return self.terminal

    def sale_with_pinpad(
        self,
        amount,
        pinpad_mode: str = "OK",
        pinpad_status: str = "CONNECTED",
        printer_status: str | None = None,
        online: bool = True,
        idempotency_key: str | None = None,
    ):
        terminal = self._require_terminal()
        key = idempotency_key or str(uuid4())
        self.pinpad.configure(mode=pinpad_mode, status=pinpad_status)
        pin = self.pinpad.request_pin(_money(amount))
        if pin["status"] != "APPROVED":
            return {
                "authorized": False,
                "status": f"PINPAD_{pin['status']}",
                "pinpad_status": pin["status"],
                "payment": None,
                "idempotency_key": key,
                "print_status": "NOT_PRINTED",
            }

        if online:
            terminal.go_online()
        else:
            terminal.go_offline()
        if printer_status:
            self.printer.set_status(printer_status)
        sale = terminal.start_sale(amount, idempotency_key=key)
        if "body" in sale:
            status = sale["body"]["status"]
            payment_id = sale["body"]["payment_id"]
        else:
            status = sale["status"]
            payment_id = None

        receipt = {
            "receipt_id": payment_id or key,
            "idempotency_key": key,
            "terminal_id": terminal.terminal_id,
            "amount": _money(amount),
            "status": status,
        }
        print_result = self.printer.print_receipt(receipt)
        return {
            "authorized": True,
            "status": status,
            "payment": sale,
            "payment_id": payment_id,
            "print_status": print_result["status"],
            "idempotency_key": key,
        }

    def hardware_go_offline(self):
        return self._require_terminal().go_offline()

    def hardware_go_online(self):
        return self._require_terminal().go_online()

    def hardware_sync(self):
        return self._require_terminal().sync()

    def hardware_queue_size(self) -> int:
        return self._require_terminal().queue_size()

    def set_printer_status(self, status: str):
        return self.printer.set_status(status)

    def refill_printer(self):
        return self.printer.refill()

    def reconnect_printer(self):
        return self.printer.reconnect()

    def reprint_pending(self):
        return self.printer.reprint_pending()

    def printer_pending_count(self) -> int:
        return self.printer.pending_count()

    def printer_printed_count(self) -> int:
        return self.printer.printed_count()

    def reboot_terminal(self):
        lifecycle = self.lifecycle.reboot()
        state = self._require_terminal().restart()
        lifecycle["queue_size"] = state["queue_size"]
        return lifecycle

    def update_firmware(self, version: str):
        return self.lifecycle.update_firmware(version)

    def update_config(self, key: str, value: str):
        return self.lifecycle.update_config(key, value)

    def firmware_version(self) -> str:
        return self.lifecycle.firmware_version

    def config_value(self, key: str) -> str:
        return str(self.lifecycle.config.get(key, ""))
