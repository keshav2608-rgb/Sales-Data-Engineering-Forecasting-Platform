#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Sales Data Engineering Platform: Setup =="

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example (edit it to enable BigQuery cloud mode)."
fi

echo "Installing Python dependencies..."
pip install --break-system-packages -r requirements.txt

echo "Setup complete."
echo "Next: make pipeline"
