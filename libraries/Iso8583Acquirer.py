"""Robot library: ISO 8583 message-flow lab."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso8583_lab.acquirer import Acquirer  # noqa: E402


class Iso8583Acquirer:
    def __init__(self) -> None:
        self._acquirer = Acquirer()

    def reset_acquirer(self) -> None:
        self._acquirer.reset()

    def process_message(self, raw: str):
        return self._acquirer.process(raw)

    def transaction_count(self) -> int:
        return len(self._acquirer.transactions)
