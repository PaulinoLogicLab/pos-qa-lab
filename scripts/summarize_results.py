"""Summarize a Robot output.xml into JSON and a small Markdown table."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "reports" / "robot" / "output.xml"
    if not output.exists():
        print(f"output.xml nao encontrado: {output}")
        return 1

    tree = ET.parse(output)
    root = tree.getroot()
    tests = []
    for test in root.iter("test"):
        status = test.find("status")
        status_name = status.attrib.get("status", "UNKNOWN") if status is not None else "UNKNOWN"
        elapsed = float(status.attrib.get("elapsed", "0")) if status is not None else 0.0
        tests.append(
            {
                "name": test.attrib.get("name", ""),
                "status": status_name,
                "elapsed_seconds": round(elapsed, 3),
            }
        )

    counts = Counter(item["status"] for item in tests)
    total_seconds = round(sum(item["elapsed_seconds"] for item in tests), 2)
    suites = []
    for suite in root.iter("suite"):
        direct_tests = suite.findall("test")
        if not direct_tests:
            continue
        suite_counts = Counter(
            test.find("status").attrib.get("status", "UNKNOWN") for test in direct_tests
        )
        suite_seconds = round(
            sum(float(test.find("status").attrib.get("elapsed", "0")) for test in direct_tests),
            3,
        )
        suites.append(
            {
                "name": suite.attrib.get("name", ""),
                "total": len(direct_tests),
                "passed": suite_counts.get("PASS", 0),
                "failed": suite_counts.get("FAIL", 0),
                "skipped": suite_counts.get("SKIP", 0),
                "elapsed_seconds": suite_seconds,
            }
        )

    summary = {
        "total": len(tests),
        "passed": counts.get("PASS", 0),
        "failed": counts.get("FAIL", 0),
        "skipped": counts.get("SKIP", 0),
        "elapsed_seconds": total_seconds,
        "suites": suites,
        "tests": tests,
    }
    target = output.parent / "summary.json"
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("| Metrica | Valor |")
    print("|---|---:|")
    print(f"| Casos | {summary['total']} |")
    print(f"| Aprovados | {summary['passed']} |")
    print(f"| Reprovados | {summary['failed']} |")
    print(f"| Ignorados | {summary['skipped']} |")
    print(f"| Tempo total | {summary['elapsed_seconds']} s |")
    print()
    print("| Suite | Casos | Aprovados | Reprovados | Tempo |")
    print("|---|---:|---:|---:|---:|")
    for suite in suites:
        print(
            f"| {suite['name']} | {suite['total']} | {suite['passed']} | "
            f"{suite['failed']} | {suite['elapsed_seconds']} s |"
        )
    print(f"\nResumo salvo em {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
