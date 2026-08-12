#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Running full pipeline =="
python3 -m pipeline.pipeline

echo ""
echo "== Running test suite =="
python3 -m pytest tests/ -v

echo ""
echo "== Done. See docs/ for architecture and dashboard/README.md for BI setup. =="
