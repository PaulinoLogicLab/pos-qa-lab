"""Start the API and run Robot suites in parallel with Pabot."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from run_suite import ROOT, wait_for_api

REPORTS = ROOT / "reports" / "pabot"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--processes", type=int, default=4)
    parser.add_argument("--suite", default=str(ROOT / "robot" / "suites"))
    parser.add_argument("--outputdir", default=str(REPORTS))
    parser.add_argument("--include", default=None)
    parser.add_argument("--exclude", default="device")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    outputdir = Path(args.outputdir)
    outputdir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env.setdefault("POS_QA_DB", str(ROOT / "data" / "pos_qa.db"))
    evidence_dir = outputdir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for stale in evidence_dir.glob("events-*.jsonl"):
        stale.unlink()
    env["ROBOT_EVIDENCE_DIR"] = str(evidence_dir)

    api_log = (outputdir / "api.log").open("w", encoding="utf-8")
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
        print("API nao iniciou.")
        api_process.terminate()
        api_log.close()
        return 1

    command = [
        sys.executable,
        "-m",
        "pabot.pabot",
        "--processes",
        str(args.processes),
        "--outputdir",
        str(outputdir),
        "--listener",
        str(ROOT / "libraries" / "RobotListener.py"),
    ]
    if args.include:
        command += ["--include", args.include]
    if args.exclude:
        command += ["--exclude", args.exclude]
    command.append(str(args.suite))

    try:
        result = subprocess.run(command, cwd=ROOT, env=env)
        return result.returncode
    finally:
        api_process.terminate()
        try:
            api_process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            api_process.kill()
        api_log.close()


if __name__ == "__main__":
    raise SystemExit(main())
