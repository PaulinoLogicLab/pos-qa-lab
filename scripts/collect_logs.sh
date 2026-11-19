#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

timestamp="$(date +%Y%m%d-%H%M%S)"
mkdir -p reports/bundle
for directory in reports/robot reports/pabot reports/device_run reports/logcat; do
  if [ -d "$directory" ]; then
    cp -R "$directory" reports/bundle/
  fi
done

tar -czf "reports/pos-qa-evidence-${timestamp}.tar.gz" -C reports bundle
rm -rf reports/bundle
echo "Evidence: reports/pos-qa-evidence-${timestamp}.tar.gz"
