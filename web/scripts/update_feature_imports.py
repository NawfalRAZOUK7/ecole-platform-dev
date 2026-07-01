#!/usr/bin/env python3
"""
Update feature API files and index.ts to import types from entities instead of local model.
"""

import re
from pathlib import Path

BASE = Path("/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/web/src")
FEATURES = BASE / "features"

# Mapping: (feature_api_path, old_import_pattern, entity_import_path)
# old_import_pattern is the regex to match the import line(s)
UPDATES = [
    # sync
    (
        FEATURES / "sync/api/sync.api.ts",
        r"from ['\"]\.\./model/sync\.types['\"]",
        "@/entities/sync/model/types",
    ),
    # attendance
    (
        FEATURES / "academic/attendance/api/attendance.api.ts",
        r"from ['\"]\.\./model/attendance\.types['\"]",
        "@/entities/academic/attendance/model/types",
    ),
    # gradebook
    (
        FEATURES / "academic/gradebook/api/gradebook.api.ts",
        r"from ['\"]\.\./model/gradebook\.types['\"]",
        "@/entities/academic/gradebook/model/types",
    ),
    # skills
    (
        FEATURES / "academic/skills/api/skills.api.ts",
        r"from ['\"]\.\./model/skills\.types['\"]",
        "@/entities/academic/skills/model/types",
    ),
    # compliance
    (
        FEATURES / "admin/compliance/api/compliance.api.ts",
        r"from ['\"]\.\./model/compliance\.types['\"]",
        "@/entities/admin/compliance/model/types",
    ),
    # budgets
    (
        FEATURES / "billing/budgets/api/budgets.api.ts",
        r"from ['\"]\.\./model/budgets\.types['\"]",
        "@/entities/billing/budget/model/types",
    ),
    # calendar
    (
        FEATURES / "communication/calendar/api/calendar.api.ts",
        r"from ['\"]\.\./model/types['\"]",
        "@/entities/communication/calendar/model/types",
    ),
    # cms
    (
        FEATURES / "content/cms/api/cms.api.ts",
        r"from ['\"]\.\./model/content-upload\.types['\"]",
        "@/entities/content/cms/model/types",
    ),
    # question-bank
    (
        FEATURES / "lms/question-bank/api/question-bank.api.ts",
        r"from ['\"]\.\./model/question-bank\.types['\"]",
        "@/entities/lms/question-bank/model/types",
    ),
    # rubrics
    (
        FEATURES / "lms/rubrics/api/rubrics.api.ts",
        r"from ['\"]\.\./model/rubrics\.types['\"]",
        "@/entities/lms/rubric/model/types",
    ),
    # financial-health
    (
        FEATURES / "reports/financial-health/api/financial-health.api.ts",
        r"from ['\"]\.\./model/financial-health\.types['\"]",
        "@/entities/reports/financial-health/model/types",
    ),
    # micro-schools
    (
        FEATURES / "school/micro-schools/api/micro-schools.api.ts",
        r"from ['\"]\.\./model/micro-schools\.types['\"]",
        "@/entities/school/micro-school/model/types",
    ),
]

for api_path, old_pattern, entity_path in UPDATES:
    if not api_path.exists():
        print(f"SKIP (not found): {api_path}")
        continue
    content = api_path.read_text(encoding="utf-8")
    new_content = re.sub(old_pattern, f'from "{entity_path}"', content)
    if new_content != content:
        api_path.write_text(new_content, encoding="utf-8")
        print(f"UPDATED: {api_path}")
    else:
        print(f"NO CHANGE: {api_path}")

# Update feature index.ts files to re-export types from entities
INDEX_UPDATES = [
    (FEATURES / "sync/index.ts", "./model/sync.types", "@/entities/sync/model/types"),
    (FEATURES / "academic/attendance/index.ts", "./model/attendance.types", "@/entities/academic/attendance/model/types"),
    (FEATURES / "academic/gradebook/index.ts", "./model/gradebook.types", "@/entities/academic/gradebook/model/types"),
    (FEATURES / "academic/skills/index.ts", "./model/skills.types", "@/entities/academic/skills/model/types"),
    (FEATURES / "admin/compliance/index.ts", "./model/compliance.types", "@/entities/admin/compliance/model/types"),
    (FEATURES / "billing/budgets/index.ts", "./model/budgets.types", "@/entities/billing/budget/model/types"),
    (FEATURES / "communication/calendar/index.ts", "./model/calendar.types", "@/entities/communication/calendar/model/types"),
    (FEATURES / "content/cms/index.ts", "./model/quiz-builder.types", "@/entities/content/cms/model/types"),
    (FEATURES / "lms/question-bank/index.ts", "./model/question-bank.types", "@/entities/lms/question-bank/model/types"),
    (FEATURES / "lms/rubrics/index.ts", "./model/rubrics.types", "@/entities/lms/rubric/model/types"),
    (FEATURES / "reports/financial-health/index.ts", "./model/financial-health.types", "@/entities/reports/financial-health/model/types"),
    (FEATURES / "school/micro-schools/index.ts", "./model/micro-schools.types", "@/entities/school/micro-school/model/types"),
]

print("\n--- Updating feature index.ts barrels ---")
for idx_path, old_rel, entity_path in INDEX_UPDATES:
    if not idx_path.exists():
        print(f"SKIP (not found): {idx_path}")
        continue
    content = idx_path.read_text(encoding="utf-8")
    # Replace export from local model with export from entity
    # e.g., export * from './model/sync.types'; → export * from '@/entities/sync/model/types';
    new_content = re.sub(
        rf"export \* from ['\"]{re.escape(old_rel)}['\"];",
        f'export * from "{entity_path}";',
        content,
    )
    if new_content != content:
        idx_path.write_text(new_content, encoding="utf-8")
        print(f"UPDATED: {idx_path}")
    else:
        print(f"NO CHANGE: {idx_path}")

print("\nDone.")
