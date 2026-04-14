#!/usr/bin/env python3
"""Export the OpenAPI spec from the running FastAPI app to docs/openapi.json.

Phase 3A — OpenAPI Spec Export & API Documentation
Usage:
    python scripts/export_openapi.py                  # export to docs/openapi.json
    python scripts/export_openapi.py --check          # CI drift detection (exit 1 if differs)
    python scripts/export_openapi.py --redoc           # also generate docs/api.html

The spec version is pinned to app.version from FastAPI config.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add backend root to path so we can import app
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402

SPEC_PATH = BACKEND_DIR / "docs" / "openapi.json"
REDOC_PATH = BACKEND_DIR / "docs" / "api.html"


def export_spec() -> dict:
    """Generate and write the OpenAPI spec to docs/openapi.json."""
    spec = app.openapi()

    SPEC_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPEC_PATH.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"OpenAPI spec exported to {SPEC_PATH}")
    return spec


def check_drift() -> bool:
    """Compare the generated spec against the committed version. Returns True if they match."""
    spec = app.openapi()
    generated = json.dumps(spec, indent=2, ensure_ascii=False) + "\n"

    if not SPEC_PATH.exists():
        print(
            f"ERROR: {SPEC_PATH} does not exist. Run 'python scripts/export_openapi.py' first."
        )
        return False

    committed = SPEC_PATH.read_text(encoding="utf-8")

    if generated != committed:
        print(f"ERROR: OpenAPI spec drift detected. {SPEC_PATH} is out of date.")
        print("Run 'make openapi' to regenerate, then commit the updated spec.")
        return False

    print(f"OK: {SPEC_PATH} is up to date.")
    return True


def generate_redoc(spec: dict | None = None) -> None:
    """Generate a static Redoc HTML page from the OpenAPI spec."""
    if spec is None:
        spec = app.openapi()

    spec_json = json.dumps(spec, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>École Platform API — {spec.get("info", {}).get("version", "0.1.0")}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet" />
    <style>body {{ margin: 0; padding: 0; }}</style>
</head>
<body>
    <div id="redoc-container"></div>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
    <script>
        const spec = {spec_json};
        Redoc.init(spec, {{
            theme: {{
                colors: {{ primary: {{ main: "#1a73e8" }} }},
                typography: {{ fontFamily: "Inter, sans-serif" }},
            }},
            hideDownloadButton: false,
            expandResponses: "200",
        }}, document.getElementById("redoc-container"));
    </script>
</body>
</html>
"""
    REDOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    REDOC_PATH.write_text(html, encoding="utf-8")
    print(f"Redoc HTML exported to {REDOC_PATH}")


def main() -> None:
    args = set(sys.argv[1:])

    if "--check" in args:
        if not check_drift():
            sys.exit(1)
        return

    spec = export_spec()

    if "--redoc" in args:
        generate_redoc(spec)
    else:
        # Always generate redoc alongside the spec
        generate_redoc(spec)

    print(f"API version: {spec.get('info', {}).get('version', '?')}")
    paths = spec.get("paths", {})
    endpoint_count = sum(len(methods) for methods in paths.values())
    print(f"Endpoints: {endpoint_count} across {len(paths)} paths")


if __name__ == "__main__":
    main()
