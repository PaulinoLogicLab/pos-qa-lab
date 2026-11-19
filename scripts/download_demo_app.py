"""Download the latest two Sauce Labs My Demo App APKs for local device tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "device" / "apps"
API = "https://api.github.com/repos/saucelabs/my-demo-app-android/releases"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    response = requests.get(API, params={"per_page": 10}, timeout=30)
    response.raise_for_status()
    releases = [item for item in response.json() if not item.get("draft")]
    selected = []
    for release in releases:
        apk = next(
            (
                asset
                for asset in release.get("assets", [])
                if asset["name"].endswith(".apk") and "androidTest" not in asset["name"]
            ),
            None,
        )
        if apk:
            selected.append((release["tag_name"], apk))
        if len(selected) == 2:
            break
    if len(selected) < 2:
        print("Nao encontrei duas releases com APK.")
        return 1

    manifest = []
    for tag, asset in selected:
        target = TARGET / asset["name"]
        print(f"Baixando {asset['browser_download_url']}")
        with requests.get(asset["browser_download_url"], stream=True, timeout=120) as stream:
            stream.raise_for_status()
            with target.open("wb") as handle:
                for chunk in stream.iter_content(chunk_size=1024 * 1024):
                    handle.write(chunk)
        actual = sha256(target)
        expected = asset.get("digest", "").replace("sha256:", "")
        if expected and actual != expected:
            print(f"Hash divergente para {target}")
            return 1
        manifest.append(
            {
                "tag": tag,
                "file": str(target),
                "sha256": actual,
                "size": target.stat().st_size,
            }
        )

    (TARGET / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
