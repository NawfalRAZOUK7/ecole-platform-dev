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
"$PYTHON_BIN" -c "
from app.main import app
import json
spec = app.openapi()
with open('openapi.json', 'w') as f:
    json.dump(spec, f, indent=2)
"
