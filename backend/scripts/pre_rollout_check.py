#!/usr/bin/env python3
"""Pre-rollout verification script for Phase 8 (direct-to-MinIO upload).

Run from the backend directory with the venv active:
    PYTHONPATH=. python scripts/pre_rollout_check.py

Each check prints PASS or FAIL.  Exit code is 0 only when all checks pass.
"""

from __future__ import annotations

import sys

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results: list[bool] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    results.append(ok)
    status = PASS if ok else FAIL
    suffix = f" — {detail}" if detail else ""
    print(f"  [{status}] {label}{suffix}")


# ---------------------------------------------------------------------------
# 1. Alembic — exactly one head
# ---------------------------------------------------------------------------
print("\n[1] Alembic migration chain")
try:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config("alembic.ini")
    scripts = ScriptDirectory.from_config(cfg)
    heads = scripts.get_heads()
    check("Exactly one Alembic head", len(heads) == 1, str(heads))
except Exception as exc:
    check("Alembic head check", False, str(exc))

# ---------------------------------------------------------------------------
# 2. Worker tasks registered
# ---------------------------------------------------------------------------
print("\n[2] ARQ worker task registration")
try:
    from app.core.tasks import WorkerSettings

    fn_names = [f.__name__ for f in WorkerSettings.functions]
    check(
        "task_post_upload_scan registered",
        "task_post_upload_scan" in fn_names,
    )
    check(
        "task_cleanup_orphaned_uploads registered",
        "task_cleanup_orphaned_uploads" in fn_names,
    )
except Exception as exc:
    check("Worker tasks", False, str(exc))

# ---------------------------------------------------------------------------
# 3. Prometheus metrics
# ---------------------------------------------------------------------------
print("\n[3] Prometheus metrics")
try:
    from prometheus_client import generate_latest

    from app.core.metrics import REGISTRY

    # Internal collector name (no _total suffix — prometheus_client adds it)
    collector_names = [m.name for m in REGISTRY.collect()]
    check(
        "virus_scan_result collector registered",
        "virus_scan_result" in collector_names,
    )

    # Exposition output must contain _total suffix
    exposition = generate_latest(REGISTRY).decode()
    check(
        "virus_scan_result_total present in /metrics output",
        "virus_scan_result_total" in exposition,
    )
except Exception as exc:
    check("Prometheus metrics", False, str(exc))

# ---------------------------------------------------------------------------
# 4. UploadSession model importable
# ---------------------------------------------------------------------------
print("\n[4] Model imports")
try:
    from app.models.uploads import UploadSession  # noqa: F401

    check("app.models.uploads.UploadSession importable", True)
except Exception as exc:
    check("UploadSession import", False, str(exc))

# ---------------------------------------------------------------------------
# 5. Schemas importable
# ---------------------------------------------------------------------------
try:
    from app.schemas.uploads import (  # noqa: F401
        CompleteUploadRequest,
        InitUploadRequest,
        UploadStatusResponse,
    )

    check("app.schemas.uploads importable", True)
except Exception as exc:
    check("Schemas import", False, str(exc))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
total = len(results)
passed = sum(results)
print(f"\n{'=' * 50}")
print(f"  {passed}/{total} checks passed")
if passed == total:
    print(f"  {PASS} — safe to proceed with rollout")
    sys.exit(0)
else:
    print(f"  {FAIL} — resolve failures before rolling out")
    sys.exit(1)
