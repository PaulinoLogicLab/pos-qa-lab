"""Start the simulated API, run Robot, and stop the API."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "robot"


def wait_for_api(url: str, timeout: float = 25.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(f"{url}/health", timeout=1)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.4)
    return False


def api_is_up(url: str) -> bool:
    try:
        return requests.get(f"{url}/health", timeout=1).status_code == 200
    except requests.RequestException:
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default=None, help="Suite path (default: robot/suites)")
    parser.add_argument("--include", default=None)
    parser.add_argument("--exclude", default=None)
    parser.add_argument("--outputdir", default=str(REPORTS))
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--device", action="store_true", help="Run robot/device instead")
    parser.add_argument("--no-api", action="store_true")
    args = parser.parse_args()

    suite = Path(args.suite) if args.suite else ROOT / (
        "robot/device" if args.device else "robot/suites"
    )
    outputdir = Path(args.outputdir)
    outputdir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("POS_QA_DB", str(ROOT / "data" / "pos_qa.db"))
    evidence_dir = outputdir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for stale in evidence_dir.glob("events-*.jsonl"):
        stale.unlink()
    env["ROBOT_EVIDENCE_DIR"] = str(evidence_dir)

    api_process = None
    api_log = None
    if not args.no_api:
        api_url = f"http://127.0.0.1:{args.port}"
        if api_is_up(api_url):
            print(
                f"Ja existe uma API respondendo em {api_url}. "
                "Pare o container/processo ou use --no-api."
            )
            return 1
        api_log_path = outputdir / "api.log"
        api_log = api_log_path.open("w", encoding="utf-8")
        api_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "src.api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(args.port),
            ],
            cwd=ROOT,
            env=env,
            stdout=api_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if not wait_for_api(f"http://127.0.0.1:{args.port}"):
            api_log.flush()
            print("API nao iniciou. Ultimas linhas:\n" + api_log_path.read_text(encoding="utf-8"))
            api_process.terminate()
            api_log.close()
            return 1

    robot_command = [
        sys.executable,
        "-m",
        "robot",
        "--outputdir",
        str(outputdir),
        "--report",
        "report.html",
        "--log",
        "log.html",
        "--listener",
        str(ROOT / "libraries" / "RobotListener.py"),
    ]
    if args.include:
        robot_command += ["--include", args.include]
    if args.exclude:
        robot_command += ["--exclude", args.exclude]
    robot_command.append(str(suite))

    try:
        result = subprocess.run(robot_command, cwd=ROOT, env=env)
        return result.returncode
    finally:
        if api_process is not None:
            api_process.terminate()
            try:
                api_process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                api_process.kill()
            if api_log is not None:
                api_log.close()


if __name__ == "__main__":
    raise SystemExit(main())
