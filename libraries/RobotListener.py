"""Robot listener that records one JSONL evidence row per test."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path


class RobotListener:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, output_dir: str | None = None) -> None:
        base = Path(
            output_dir
            or os.getenv("ROBOT_EVIDENCE_DIR", "reports/evidence")
        )
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / f"events-{os.getpid()}.jsonl"

    def start_test(self, data, result) -> None:
        self._write(
            {
                "event": "start_test",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "name": data.name,
                "tags": list(data.tags),
            }
        )

    def end_test(self, data, result) -> None:
        self._write(
            {
                "event": "end_test",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "name": data.name,
                "tags": list(data.tags),
                "status": result.status,
                "message": result.message,
                "elapsed_ms": result.elapsedtime,
            }
        )

    def _write(self, record: dict) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
