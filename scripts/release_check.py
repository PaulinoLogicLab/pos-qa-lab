"""Release readiness checks for the POS QA Lab v1.0.0.

Run after the local suites and k6:
    python scripts/release_check.py
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILURES: list[str] = []
SKIPS: list[str] = []
RESULTS: list[tuple[str, str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        RESULTS.append((name, "PASS", detail))
    else:
        FAILURES.append(name)
        RESULTS.append((name, "FAIL", detail))


def skip(name: str, detail: str) -> None:
    SKIPS.append(name)
    RESULTS.append((name, "SKIP", detail))


def load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def version_from(path: Path, pattern: str) -> str | None:
    if not path.exists():
        return None
    match = re.search(pattern, path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def tracked_files() -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "ls-files"], cwd=ROOT, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return [line for line in output.splitlines() if line.strip()]


def main() -> int:
    pyproject_version = version_from(ROOT / "pyproject.toml", r'version\s*=\s*"([^"]+)"')
    app_version = version_from(ROOT / "src" / "api" / "main.py", r'version="([^"]+)"')
    check("Versao do pyproject e da API", pyproject_version == app_version == "1.0.0",
          f"pyproject={pyproject_version}, api={app_version}")

    required = [
        "README.md",
        "LICENSE",
        "Dockerfile",
        "docker-compose.yml",
        "Makefile",
        "requirements.txt",
        "docs/05_relatorio-execucao.md",
        "docs/06_relatorio-defeitos.md",
        "docs/11_metricas-qualidade.md",
        "docs/12_homologacao.md",
        "performance/payment_load.js",
        "robot/suites/10_hardware_peripherals.robot",
        "robot/device/05_device_smoke.robot",
    ]
    missing = [path for path in required if not (ROOT / path).exists()]
    check("Arquivos obrigatorios", not missing, ", ".join(missing) or "todos presentes")

    changelog = ROOT / "CHANGELOG.md"
    check(
        "Changelog v1.0.0",
        changelog.exists() and "1.0.0" in changelog.read_text(encoding="utf-8"),
    )

    core = load_json(ROOT / "reports" / "robot" / "summary.json")
    if core is None:
        skip("Resumo do nucleo", "reports/robot/summary.json ausente")
    else:
        check(
            "Nucleo 44/44",
            int(core.get("total", 0)) >= 44
            and core.get("passed") == core.get("total")
            and core.get("failed") == 0,
            f"{core.get('passed')}/{core.get('total')}",
        )

    pabot = load_json(ROOT / "reports" / "pabot" / "summary.json")
    if pabot is None:
        skip("Resumo do Pabot", "reports/pabot/summary.json ausente")
    else:
        check(
            "Pabot 44/44",
            pabot.get("passed") == pabot.get("total")
            and pabot.get("failed") == 0
            and int(pabot.get("total", 0)) >= 44,
            f"{pabot.get('passed')}/{pabot.get('total')}",
        )

    k6 = load_json(ROOT / "reports" / "k6-summary.json")
    if k6 is None:
        skip("Resumo do k6", "reports/k6-summary.json ausente")
    else:
        check(
            "k6 thresholds",
            bool(k6.get("thresholds_passed")),
            (
                f"req={k6.get('requests')}, p95={k6.get('p95_ms')}ms, "
                f"failed={k6.get('http_failed_rate')}"
            ),
        )

    device = load_json(ROOT / "reports" / "device_run" / "summary.json")
    if device is None:
        skip("Resumo do device", "reports/device_run/summary.json ausente")
    else:
        check(
            "Device 5/5",
            device.get("passed") == device.get("total") and device.get("failed") == 0,
            f"{device.get('passed')}/{device.get('total')}",
        )

    files = tracked_files()
    if not files:
        skip("Arquivos versionados", "git ls-files indisponivel")
    else:
        forbidden = [
            path
            for path in files
            if path.lower().endswith((".apk", ".aab"))
            or path in {".env", "device/apps/manifest.json"}
        ]
        check("Sem APK ou .env versionado", not forbidden, ", ".join(forbidden) or "ok")
        secret_patterns = ("ghp_", "gho_", "github_pat_", "BEGIN RSA PRIVATE KEY")
        suspicious = []
        for path in files:
            if path.lower().endswith((".png", ".jpg", ".pdf", ".zip", ".gz")):
                continue
            try:
                text = (ROOT / path).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if any(pattern in text for pattern in secret_patterns):
                suspicious.append(path)
        check("Sem segredo obvio versionado", not suspicious, ", ".join(suspicious) or "ok")

    print(f"{'CHECK':40} {'STATUS':6} DETAIL")
    print("-" * 80)
    for name, status, detail in RESULTS:
        print(f"{name:40} {status:6} {detail}")
    print("-" * 80)
    if FAILURES:
        print(f"FAIL: {len(FAILURES)} verificacao(oes) falharam.")
        return 1
    print(f"GO: {len(RESULTS) - len(SKIPS)} verificacoes passaram, {len(SKIPS)} ignoradas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
