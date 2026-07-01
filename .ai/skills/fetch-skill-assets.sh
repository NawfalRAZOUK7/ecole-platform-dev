#!/usr/bin/env bash
# Bootstrap: pull non-vendored skill assets (references, scripts, data, fonts)
# from upstream repos into .ai/skills/. Run ONCE from anywhere:
#   bash ecole-platform-dev/.ai/skills/fetch-skill-assets.sh
# Idempotent: re-running refreshes assets. Adapted SKILL.md files are preserved.
set -euo pipefail

SKILLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fetch_repo() { # owner/repo ref -> extracted dir path on stdout
  local repo="$1" ref="${2:-main}"
  local slug="${repo//\//-}"
  if [ ! -d "$TMP/$slug" ]; then
    echo "Downloading $repo@$ref ..." >&2
    curl -fsSL "https://codeload.github.com/$repo/tar.gz/refs/heads/$ref" -o "$TMP/$slug.tgz"
    mkdir -p "$TMP/$slug"
    tar -xzf "$TMP/$slug.tgz" -C "$TMP/$slug" --strip-components=1
  fi
  echo "$TMP/$slug"
}

copy_subdirs() { # src_skill_dir dst_skill_dir subdir...
  local src="$1" dst="$2"; shift 2
  mkdir -p "$dst"
  for sub in "$@"; do
    [ -d "$src/$sub" ] && { mkdir -p "$dst/$sub"; cp -R "$src/$sub/." "$dst/$sub/"; echo "  + $dst/$sub"; }
  done
  return 0
}

# ---------------------------------------------------------------------------
# 1. nextlevelbuilder/ui-ux-pro-max-skill  (design suite assets)
# ---------------------------------------------------------------------------
UIUX="$(fetch_repo nextlevelbuilder/ui-ux-pro-max-skill)"
US="$UIUX/.claude/skills"

copy_subdirs "$US/brand"          "$SKILLS_DIR/brand"          references scripts templates
copy_subdirs "$US/design"         "$SKILLS_DIR/design"         references scripts data
copy_subdirs "$US/design-system"  "$SKILLS_DIR/design-system"  references scripts data templates
copy_subdirs "$US/slides"         "$SKILLS_DIR/slides"         references
copy_subdirs "$US/banner-design"  "$SKILLS_DIR/banner-design"  references
copy_subdirs "$US/ui-styling"     "$SKILLS_DIR/ui-styling"     references scripts canvas-fonts
# search CLI + databases used by ui-ux-pro-max SKILL.md
[ -d "$UIUX/cli" ] && { mkdir -p "$SKILLS_DIR/ui-ux-pro-max/cli"; cp -R "$UIUX/cli/." "$SKILLS_DIR/ui-ux-pro-max/cli/"; echo "  + ui-ux-pro-max/cli"; }
# upstream search.py path, if shipped inside the skill folder
copy_subdirs "$US/ui-ux-pro-max"  "$SKILLS_DIR/ui-ux-pro-max"  scripts data references

# ---------------------------------------------------------------------------
# 2. Agents365-ai/365-skills  (mermaid syntax references)
# ---------------------------------------------------------------------------
A365="$(fetch_repo Agents365-ai/365-skills)"
copy_subdirs "$A365/plugins/mermaid/skills/mermaid-skill" "$SKILLS_DIR/mermaid-diagrams" reference references

# ---------------------------------------------------------------------------
# 3. evanca/flutter-ai-rules  (extra skills installed verbatim, per user choice)
#    NOTE: bloc/provider/change-notifier/mockito describe patterns COMPETING with
#    the project standard (Riverpod + mocktail). Only follow them when explicitly
#    working with that pattern, never by default.
# ---------------------------------------------------------------------------
FAR="$(fetch_repo evanca/flutter-ai-rules)"
for s in bloc provider flutter-change-notifier mockito patrol-e2e-testing \
         flutter-pre-caching architecture-feature-first flutterfire-configure \
         firebase-ai firebase-analytics firebase-app-check firebase-auth \
         firebase-cloud-firestore firebase-cloud-functions firebase-crashlytics \
         firebase-data-connect firebase-database firebase-in-app-messaging \
         firebase-messaging firebase-remote-config firebase-storage; do
  if [ -d "$FAR/skills/$s" ]; then
    mkdir -p "$SKILLS_DIR/$s"; cp -R "$FAR/skills/$s/." "$SKILLS_DIR/$s/"; echo "  + $s"
  fi
done

# ---------------------------------------------------------------------------
# 4. kevmoo/dash_skills  (extra micro-skills, per user choice)
#    dart-best-practices and dart-modern-features are NOT copied — their content
#    was merged into effective-dart and dart-3-updates locally.
# ---------------------------------------------------------------------------
DASH="$(fetch_repo kevmoo/dash_skills)"
for s in dart-doc-validation dart-long-lines dart-multiline-strings dart-package-maintenance; do
  if [ -d "$DASH/skills/$s" ]; then
    mkdir -p "$SKILLS_DIR/$s"; cp -R "$DASH/skills/$s/." "$SKILLS_DIR/$s/"; echo "  + $s"
  fi
done
# upstream helper script referenced by dart-test-coverage
[ -d "$DASH/skills/dart-test-coverage/scripts" ] && copy_subdirs "$DASH/skills/dart-test-coverage" "$SKILLS_DIR/dart-test-coverage" scripts

# ---------------------------------------------------------------------------
# 5. dominikmartn/nothing-design-skill  (leftover asset)
# ---------------------------------------------------------------------------
ND="$(fetch_repo dominikmartn/nothing-design-skill)"
[ -f "$ND/preview.gif" ] && cp "$ND/preview.gif" "$SKILLS_DIR/nothing-design/preview.gif" && echo "  + nothing-design/preview.gif"

echo
echo "Done. Preserved local (adapted/merged) SKILL.md files; refreshed assets from upstream."
echo "Optional cleanup: ui-styling/canvas-fonts is ~15 MB of TTFs — delete if you never generate canvas designs."
