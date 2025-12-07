#!/usr/bin/env bash
set -euo pipefail

for d in ./repos/*; do
  if [ -d "$d/.git" ]; then
    echo "=== Scanning $d ==="
    python gha_smell_detector.py "$d"
    echo
  fi
done
