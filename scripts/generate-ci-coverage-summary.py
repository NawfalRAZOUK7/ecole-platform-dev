#!/usr/bin/env python3
"""Generate CI code-coverage and behavioral test-coverage summaries."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from xml.etree import ElementTree


TEST_FAMILIES = [
    ("lint", "Backend lint/format", "required", "behavioral", False),
    ("security-trivy", "Container image scan", "required", "security", False),
    ("security-pip-audit", "Python dependency audit", "required", "security", False),
    ("security-bandit", "Backend static security scan", "required", "security", False),
    ("migration-safety", "Migration safety", "required", "behavioral", False),
    ("unit-tests", "Backend unit tests", "required", "unit", True),
    ("integration-tests", "Backend integration API tests", "required", "integration", True),
    ("contract-tests", "Backend contract tests", "required", "contract", True),
    ("security-tests", "Backend security tests", "required", "security", True),
    ("security-audit", "Backend security audit tests", "required", "security", True),
    ("postman-tests", "Postman full collection", "required", "postman", True),
    ("postman-scenario-tests", "Postman scenario collections", "required", "postman", True),
    ("e2e-tests", "Playwright web E2E", "required", "e2e", True),
    ("k6-load-tests", "k6 auth baseline", "required", "load", False),
    ("load-tests", "k6 full baseline", "required", "load", False),
    ("cleanup-test-data", "Postman cleanup", "optional", "maintenance", False),
    ("coverage-report", "Backend coverage aggregation", "required", "coverage", True),
    ("publish-images", "Publish images", "optional", "release", False),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--needs-json", default=os.environ.get("NEEDS_JSON", "{}"))
    parser.add_argument("--backend-coverage", default="backend/coverage.xml")
    parser.add_argument("--web-coverage", default="web/coverage/coverage-final.json")
    parser.add_argument("--mobile-coverage", default="mobile/coverage/lcov.info")
    parser.add_argument("--output-json", default="test-coverage-summary.json")
    parser.add_argument("--output-md", default="test-coverage-summary.md")
    parser.add_argument("--fail-required", action="store_true")
    return parser.parse_args()


def load_needs(raw: str) -> dict[str, dict[str, object]]:
    try:
        value = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def coverage_from_xml(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    root = ElementTree.parse(path).getroot()
    line_rate = float(root.attrib.get("line-rate", 0.0)) * 100
    branch_rate = float(root.attrib.get("branch-rate", 0.0)) * 100
    return {
        "format": "cobertura",
        "path": str(path),
        "line_rate": round(line_rate, 2),
        "branch_rate": round(branch_rate, 2),
    }


def coverage_from_v8_json(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    totals = {
        "statements": [0, 0],
        "branches": [0, 0],
        "functions": [0, 0],
        "lines": [0, 0],
    }
    for item in data.values():
        if not isinstance(item, dict):
            continue
        for key, pair in (
            ("statements", ("s", "statementMap")),
            ("branches", ("b", "branchMap")),
            ("functions", ("f", "fnMap")),
            ("lines", ("s", "statementMap")),
        ):
            hits_key, map_key = pair
            hits = item.get(hits_key, {})
            total = len(item.get(map_key, {}))
            covered = sum(1 for value in hits.values() if value and value != [0])
            totals[key][0] += covered
            totals[key][1] += total

    def pct(pair: list[int]) -> float:
        return round((pair[0] / pair[1] * 100) if pair[1] else 0.0, 2)

    return {
        "format": "istanbul-json",
        "path": str(path),
        "statements": pct(totals["statements"]),
        "branches": pct(totals["branches"]),
        "functions": pct(totals["functions"]),
        "lines": pct(totals["lines"]),
    }


def coverage_from_lcov(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    found = hit = 0
    branch_found = branch_hit = 0
    for line in path.read_text(errors="ignore").splitlines():
        if line.startswith("LF:"):
            found += int(line.split(":", 1)[1])
        elif line.startswith("LH:"):
            hit += int(line.split(":", 1)[1])
        elif line.startswith("BRF:"):
            branch_found += int(line.split(":", 1)[1])
        elif line.startswith("BRH:"):
            branch_hit += int(line.split(":", 1)[1])
    return {
        "format": "lcov",
        "path": str(path),
        "line_rate": round((hit / found * 100) if found else 0.0, 2),
        "branch_rate": round((branch_hit / branch_found * 100) if branch_found else 0.0, 2),
    }


def build_summary(args: argparse.Namespace) -> dict[str, object]:
    needs = load_needs(args.needs_json)
    families = []
    for job_id, name, requirement, category, contributes_code_coverage in TEST_FAMILIES:
        result = str(needs.get(job_id, {}).get("result", "not_reported"))
        skipped_reason = ""
        if result == "skipped":
            skipped_reason = (
                "Optional/manual gate or upstream/path/branch condition skipped it."
                if requirement == "optional"
                else "Required gate was skipped; inspect workflow conditions and upstream jobs."
            )
        families.append(
            {
                "id": job_id,
                "name": name,
                "requirement": requirement,
                "category": category,
                "status": result,
                "skipped_reason": skipped_reason,
                "contributes_code_coverage": contributes_code_coverage,
            }
        )

    code_coverage = {
        "backend": coverage_from_xml(Path(args.backend_coverage)),
        "web_unit": coverage_from_v8_json(Path(args.web_coverage)),
        "mobile_unit": coverage_from_lcov(Path(args.mobile_coverage)),
        "web_e2e": None,
        "mobile_integration": None,
        "k8s_e2e": None,
    }
    return {"code_coverage": code_coverage, "test_coverage": families}


def write_markdown(summary: dict[str, object], path: Path) -> None:
    lines = ["# CI Coverage Summary", "", "## Code Coverage", ""]
    for name, payload in (summary["code_coverage"] or {}).items():
        if not payload:
            lines.append(f"- **{name}**: not reported")
            continue
        metrics = []
        for key in ("line_rate", "branch_rate", "lines", "branches", "functions", "statements"):
            if key in payload:
                metrics.append(f"{key.replace('_', ' ')} {payload[key]}%")
        lines.append(f"- **{name}**: {', '.join(metrics)}")

    lines.extend(["", "## Behavioral Test Coverage", "", "| Gate | Required | Status | Code coverage | Skip reason |", "| --- | --- | --- | --- | --- |"])
    for item in summary["test_coverage"]:
        lines.append(
            "| {name} | {requirement} | {status} | {coverage} | {reason} |".format(
                name=item["name"],
                requirement=item["requirement"],
                status=item["status"],
                coverage="yes" if item["contributes_code_coverage"] else "no",
                reason=item["skipped_reason"] or "",
            )
        )
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    summary = build_summary(args)
    Path(args.output_json).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    write_markdown(summary, Path(args.output_md))
    if args.fail_required:
        bad = [
            item
            for item in summary["test_coverage"]
            if item["requirement"] == "required" and item["status"] not in {"success", "not_reported"}
        ]
        if bad:
            print("Required CI gates did not succeed:")
            for item in bad:
                print(f"- {item['name']}: {item['status']}")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
