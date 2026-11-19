"""Robot library: terminal simulator with an offline queue."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.terminal.simulator import TerminalSimulator  # noqa: E402


class Terminal:
    def __init__(
        self,
        api_url: str = "http://127.0.0.1:8000",
        terminal_id: str = "TERM0001",
        db_path: str | None = None,
    ) -> None:
        self.api_url = api_url
        self.terminal_id = terminal_id
        self.db_path = db_path
        self._terminal = TerminalSimulator(api_url, terminal_id, db_path)

    def use_terminal(self, terminal_id: str, db_path: str | None = None):
        self.terminal_id = terminal_id
        self.db_path = db_path
        self._terminal = TerminalSimulator(self.api_url, terminal_id, db_path)
        return {"terminal_id": terminal_id, "db_path": str(self._terminal.db_path)}

    def go_offline(self):
        return self._terminal.go_offline()

    def go_online(self):
        return self._terminal.go_online()

    def restart(self):
        return self._terminal.restart()

    def start_sale(
        self,
        amount,
        method: str = "credit",
        installments: int = 1,
        entry_mode: str = "chip",
        card_token: str = "tok_approved",
        capture: bool = True,
        idempotency_key=None,
    ):
        return self._terminal.start_sale(
            amount=amount,
            method=method,
            installments=installments,
            entry_mode=entry_mode,
            card_token=card_token,
            capture=capture,
            idempotency_key=idempotency_key,
        )

    def queue_size(self) -> int:
        return self._terminal.queue_size()

    def queued_transactions(self):
        return self._terminal.queued_transactions()

    def sync(self):
        return self._terminal.sync()

    def get_payment(self, payment_id: str):
        return self._terminal.get_payment(payment_id)
