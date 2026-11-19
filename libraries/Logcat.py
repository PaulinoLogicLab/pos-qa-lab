"""Robot library: collect Android logcat evidence for device failures."""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


class Logcat:
    def __init__(self, output_dir: str = "reports/logcat") -> None:
        self.output_dir = Path(output_dir)

    def capture_logcat(self, lines: int = 500, package: str | None = None) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        target = self.output_dir / f"logcat-{datetime.now():%Y%m%d-%H%M%S}.txt"
        command = ["adb", "logcat", "-d", "-t", str(lines)]
        if package:
            command = ["adb", "logcat", "-d", "-t", str(lines), "--pid", self._pid(package)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        target.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        return str(target)

    def device_info(self) -> str:
        result = subprocess.run(
            ["adb", "shell", "getprop", "ro.product.model"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.stdout.strip()

    @staticmethod
    def _pid(package: str) -> str:
        result = subprocess.run(
            ["adb", "shell", "pidof", package],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.stdout.strip() or "0"
