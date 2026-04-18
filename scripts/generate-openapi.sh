#!/usr/bin/env sh
set -eu

PYTHON_BIN="${PYTHON_BIN:-python}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="python3"
fi

cd "$(dirname "$0")/../backend"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

# Keep the web contract snapshot aligned with the backend CI exporter.
"$PYTHON_BIN" scripts/export_openapi.py
cp docs/openapi.json openapi.json
