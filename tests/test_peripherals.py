from __future__ import annotations

import pytest

from src.terminal.peripherals import Pinpad, Printer, TerminalLifecycle


def test_printer_paper_out_keeps_receipt_pending():
    printer = Printer()
    printer.set_status("PAPER_OUT")
    result = printer.print_receipt({"receipt_id": "r1", "amount": "10.00"})
    assert result["status"] == "PAPER_OUT"
    assert printer.pending_count() == 1
    assert printer.printed_count() == 0

    printer.refill()
    reprint = printer.reprint_pending()
    assert reprint["reprinted"] == 1
    assert printer.pending_count() == 0
    assert printer.printed_count() == 1


def test_printer_offline_requires_reconnect():
    printer = Printer()
    printer.set_status("OFFLINE")
    assert printer.print_receipt({"receipt_id": "r2"})["status"] == "OFFLINE"
    assert printer.reprint_pending()["reprinted"] == 0

    printer.reconnect()
    assert printer.reprint_pending()["reprinted"] == 1


def test_pinpad_timeout_and_cancel():
    pinpad = Pinpad()
    pinpad.configure(mode="TIMEOUT")
    assert pinpad.request_pin("10.00")["status"] == "TIMEOUT"
    pinpad.configure(mode="CANCELLED")
    assert pinpad.request_pin("10.00")["status"] == "CANCELLED"


def test_pinpad_disconnected_has_priority():
    pinpad = Pinpad()
    pinpad.configure(mode="TIMEOUT", status="DISCONNECTED")
    assert pinpad.request_pin("10.00")["status"] == "DISCONNECTED"


def test_lifecycle_reboot_and_update():
    lifecycle = TerminalLifecycle()
    assert lifecycle.firmware_version == "1.0.0"
    lifecycle.reboot()
    assert lifecycle.boot_count == 1
    lifecycle.update_firmware("1.1.0")
    lifecycle.update_config("display_language", "en-US")
    assert lifecycle.firmware_version == "1.1.0"
    assert lifecycle.config["display_language"] == "en-US"


def test_invalid_printer_status_is_rejected():
    with pytest.raises(ValueError, match="invalid printer status"):
        Printer().set_status("EXPLODED")
