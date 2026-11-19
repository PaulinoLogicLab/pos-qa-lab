"""Install an old APK, upgrade with a new APK and collect device evidence.

This is the executable evidence for CT-DEV-01 (install/update). It does not
replace a full Appium suite; it checks that the package survives an in-place
upgrade and that logcat is preserved for analysis.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "com.saucelabs.mydemoapp.android"
ACTIVITY = ".view.activities.SplashActivity"


def adb(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["adb", *args], capture_output=True, text=True, timeout=timeout)


def require_device() -> None:
    result = adb("devices")
    lines = [line for line in result.stdout.splitlines() if "\tdevice" in line]
    if not lines:
        raise SystemExit("Nenhum dispositivo/emulador conectado (adb devices vazio).")


def install(apk: Path) -> None:
    result = adb("install", "-r", str(apk), timeout=180)
    if result.returncode != 0 or "Success" not in result.stdout:
        raise SystemExit(f"Falha ao instalar {apk}:\n{result.stdout}\n{result.stderr}")


def launch() -> None:
    adb("shell", "am", "force-stop", PACKAGE)
    adb("shell", "am", "start", "-n", f"{PACKAGE}/{ACTIVITY}")
    time.sleep(4)


def running() -> bool:
    result = adb("shell", "pidof", PACKAGE)
    return bool(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--output", default=str(ROOT / "reports" / "device" / "upgrade-check.txt"))
    args = parser.parse_args()

    require_device()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Device upgrade check - {datetime.now():%Y-%m-%d %H:%M:%S}", ""]

    lines.append(f"Instalando versao antiga: {args.old.name}")
    install(args.old)
    launch()
    lines.append(f"App rodando apos instalacao antiga: {running()}")

    lines.append(f"Atualizando por cima: {args.new.name}")
    install(args.new)
    launch()
    ok = running()
    lines.append(f"App rodando apos atualizacao: {ok}")

    logcat = adb("logcat", "-d", "-t", "3000")
    logcat_file = output.with_suffix(".logcat.txt")
    logcat_file.write_text(logcat.stdout, encoding="utf-8")
    lines.append(f"Logcat: {logcat_file}")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
