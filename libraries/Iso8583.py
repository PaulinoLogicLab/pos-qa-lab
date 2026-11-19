"""Robot library: ISO 8583 lab parser and builder."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iso8583_lab.parser import (  # noqa: E402
    build_message,
    mask_pan,
    parse_message,
)


class Iso8583:
    def parse_message(self, raw: str):
        return parse_message(raw)

    def build_message(self, mti: str, fields: dict):
        return build_message(mti, fields)

    def mask_pan(self, pan: str) -> str:
        return mask_pan(pan)
