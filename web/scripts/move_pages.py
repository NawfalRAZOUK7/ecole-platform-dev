#!/usr/bin/env python3
"""
Phase 4: Move selected page components from features/ to pages/.
Rewrites relative imports to absolute paths.
"""

import re
import shutil
from pathlib import Path

BASE = Path("/Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/web/src")
FEATURES = BASE / "features"
PAGES = BASE / "pages"

PAGES_TO_MOVE = [
    # (source_path, dest_dir_in_pages, feature_name_for_rewrite)
    (FEATURES / "auth/ui/LoginPage.tsx", "auth", "auth"),
    (FEATURES / "auth/ui/ForgotPasswordPage.tsx", "auth", "auth"),
    (FEATURES / "auth/ui/ResetPasswordPage.tsx", "auth", "auth"),
    (FEATURES / "user/privacy/ui/GDPRPage.tsx", "user", "user/privacy"),
    (FEATURES / "admin/ui/FeatureTogglesPage.tsx", "admin", "admin"),
]

def rewrite_imports(content: str, feature_name: str) -> str:
    """Rewrite relative imports to absolute paths from features."""
    # ../api/X.ts → @/features/{feature}/api/X
    content = re.sub(
        rf"from ['\"]\.\./api/([^'\"]+)['\"]",
        f'from "@/features/{feature_name}/api/\\1"',
        content,
    )
    # ../model/X.ts → @/features/{feature}/model/X
    content = re.sub(
        rf"from ['\"]\.\./model/([^'\"]+)['\"]",
        f'from "@/features/{feature_name}/model/\\1"',
        content,
    )
    # ./X.tsx → @/features/{feature}/ui/X
    content = re.sub(
        rf"from ['\"]\./([^'\"]+)['\"]",
        f'from "@/features/{feature_name}/ui/\\1"',
        content,
    )
    return content

for src_path, dest_dir, feature_name in PAGES_TO_MOVE:
    if not src_path.exists():
        print(f"SKIP (not found): {src_path}")
        continue

    dest_path = PAGES / dest_dir / src_path.name
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    content = src_path.read_text(encoding="utf-8")
    new_content = rewrite_imports(content, feature_name)
    dest_path.write_text(new_content, encoding="utf-8")

    print(f"MOVED: {src_path} → {dest_path}")

# Update lazy.ts files for auth
auth_lazy = FEATURES / "auth/lazy.ts"
if auth_lazy.exists():
    content = auth_lazy.read_text(encoding="utf-8")
    content = content.replace("'./ui/LoginPage'", "'@/pages/auth/LoginPage'")
    content = content.replace("'./ui/ForgotPasswordPage'", "'@/pages/auth/ForgotPasswordPage'")
    content = content.replace("'./ui/ResetPasswordPage'", "'@/pages/auth/ResetPasswordPage'")
    auth_lazy.write_text(content, encoding="utf-8")
    print(f"UPDATED: {auth_lazy}")

# Update App.tsx for static imports
app_tsx = BASE / "app/App.tsx"
if app_tsx.exists():
    content = app_tsx.read_text(encoding="utf-8")
    content = content.replace(
        "import { FeatureTogglesPage } from '@/features/admin/ui/FeatureTogglesPage';",
        "import { FeatureTogglesPage } from '@/pages/admin/FeatureTogglesPage';",
    )
    content = content.replace(
        "import { GDPRPage } from '@/features/user/privacy/ui/GDPRPage';",
        "import { GDPRPage } from '@/pages/user/GDPRPage';",
    )
    app_tsx.write_text(content, encoding="utf-8")
    print(f"UPDATED: {app_tsx}")

# Delete old files
for src_path, _, _ in PAGES_TO_MOVE:
    if src_path.exists():
        src_path.unlink()
        print(f"DELETED: {src_path}")

# Create pages barrels
for _, dest_dir, _ in PAGES_TO_MOVE:
    barrel = PAGES / dest_dir / "index.ts"
    if not barrel.exists():
        barrel.write_text(f"// {dest_dir} pages barrel\n", encoding="utf-8")

print("\nDone.")
