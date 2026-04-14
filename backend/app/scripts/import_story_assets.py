"""Import story content assets into the platform via the existing CMS and content APIs.

Usage:
    python -m app.scripts.import_story_assets --manifest assets/stories/manifest.json
    python -m app.scripts.import_story_assets --dir assets/stories/ --base-url http://localhost:8000

Manifest format (assets/stories/manifest.json):
[
  {
    "title": "قصة الأرنب الشجاع",
    "content_type": "STORY",
    "level_band": "K1",
    "language": "ar",
    "subject": "arabic",
    "letter": "أ",
    "target_age_min": 4,
    "target_age_max": 6,
    "theme_color": "#FF6B35",
    "pages": [
      {
        "file": "rabbit_p01.jpg",
        "page_number": 1,
        "narration_text": "كان يا ما كان...",
        "has_activity": false,
        "asset_type": "illustration"
      }
    ]
  }
]

If --dir is given instead of --manifest, the script auto-discovers folders matching
the pattern: <dir>/<story_slug>/pages/*.{jpg,png,webp} and a metadata.json per story.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import mimetypes
import sys
from pathlib import Path

import httpx


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_API_PREFIX = "/api/v1"
LOGIN_ENDPOINT = "/auth/login"
CMS_CONTENT_ENDPOINT = "/cms/content"
PAGES_ENDPOINT_TPL = "/content-items/{content_id}/pages"

SUPPORTED_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
}


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


async def login(
    client: httpx.AsyncClient, base_url: str, email: str, password: str
) -> str:
    """Authenticate and return a Bearer token."""
    resp = await client.post(
        f"{base_url}{DEFAULT_API_PREFIX}{LOGIN_ENDPOINT}",
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    data = resp.json()
    # Support both {"access_token": ...} and {"data": {"access_token": ...}}
    token = data.get("access_token") or (data.get("data") or {}).get("access_token")
    if not token:
        raise RuntimeError(
            f"Could not extract access_token from login response: {data}"
        )
    return token


# ---------------------------------------------------------------------------
# Content creation
# ---------------------------------------------------------------------------


async def create_content_item(
    client: httpx.AsyncClient,
    base_url: str,
    story_meta: dict,
) -> str:
    """Create a ContentItem via POST /cms/content and return its UUID."""
    payload = {
        "title": story_meta["title"],
        "content_type": story_meta.get("content_type", "STORY"),
        "level_band": story_meta.get("level_band"),
        "language": story_meta.get("language"),
        "subject": story_meta.get("subject"),
        "description": story_meta.get("description"),
        "page_count": story_meta.get("page_count"),
        "letter": story_meta.get("letter"),
        "target_age_min": story_meta.get("target_age_min"),
        "target_age_max": story_meta.get("target_age_max"),
        "theme_color": story_meta.get("theme_color"),
        "status": story_meta.get("status", "published"),
    }
    # Remove None values so server defaults apply
    payload = {k: v for k, v in payload.items() if v is not None}

    resp = await client.post(
        f"{base_url}{DEFAULT_API_PREFIX}{CMS_CONTENT_ENDPOINT}",
        json=payload,
    )
    resp.raise_for_status()
    data = resp.json()
    content_id = data.get("id") or (data.get("data") or {}).get("id")
    if not content_id:
        raise RuntimeError(f"Could not extract id from create response: {data}")
    return content_id


async def upload_page(
    client: httpx.AsyncClient,
    base_url: str,
    content_id: str,
    page_path: Path,
    page_number: int,
    narration_text: str | None,
    has_activity: bool,
    asset_type: str,
) -> dict:
    """Upload a single story page asset."""
    suffix = page_path.suffix.lower()
    mime_type = SUPPORTED_MIME.get(suffix) or (
        mimetypes.guess_type(str(page_path))[0] or "application/octet-stream"
    )
    endpoint = f"{base_url}{DEFAULT_API_PREFIX}" + PAGES_ENDPOINT_TPL.format(
        content_id=content_id
    )

    with page_path.open("rb") as fh:
        files = {"file": (page_path.name, fh, mime_type)}
        data: dict[str, str | int] = {
            "page_number": str(page_number),
            "has_activity": str(has_activity).lower(),
            "asset_type": asset_type,
        }
        if narration_text:
            data["narration_text"] = narration_text

        resp = await client.post(endpoint, files=files, data=data)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Manifest loading
# ---------------------------------------------------------------------------


def load_manifest(manifest_path: Path) -> list[dict]:
    with manifest_path.open(encoding="utf-8") as fh:
        return json.load(fh)


def discover_from_dir(stories_dir: Path) -> list[dict]:
    """Auto-discover stories from a directory tree.

    Expected layout:
      <stories_dir>/
        <story_slug>/
          metadata.json      # story metadata (same keys as manifest entry, minus "pages")
          pages/
            001.jpg
            002.jpg
            ...
    """
    stories: list[dict] = []
    for story_dir in sorted(stories_dir.iterdir()):
        if not story_dir.is_dir():
            continue
        meta_file = story_dir / "metadata.json"
        if not meta_file.exists():
            print(f"  [SKIP] {story_dir.name}: no metadata.json")
            continue

        with meta_file.open(encoding="utf-8") as fh:
            meta = json.load(fh)

        pages_dir = story_dir / "pages"
        page_files = (
            sorted(
                p
                for p in pages_dir.iterdir()
                if p.is_file() and p.suffix.lower() in SUPPORTED_MIME
            )
            if pages_dir.exists()
            else []
        )

        meta["pages"] = [
            {
                "file": str(p),
                "page_number": i + 1,
                "narration_text": None,
                "has_activity": False,
                "asset_type": "illustration",
            }
            for i, p in enumerate(page_files)
        ]
        stories.append(meta)
    return stories


# ---------------------------------------------------------------------------
# Main import loop
# ---------------------------------------------------------------------------


async def import_stories(
    stories: list[dict],
    base_url: str,
    token: str,
    assets_root: Path | None,
    dry_run: bool,
) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    total_stories = len(stories)
    total_pages = sum(len(s.get("pages", [])) for s in stories)
    print(f"\nImporting {total_stories} stories with {total_pages} total pages...")
    print(f"  Base URL : {base_url}")
    print(f"  Dry run  : {dry_run}\n")

    async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
        for idx, story in enumerate(stories, 1):
            title = story.get("title", f"Story {idx}")
            pages = story.get("pages", [])
            print(f"[{idx}/{total_stories}] {title!r} ({len(pages)} pages)")

            if dry_run:
                print(
                    f"  [DRY RUN] Would create ContentItem and upload {len(pages)} pages"
                )
                continue

            try:
                content_id = await create_content_item(client, base_url, story)
                print(f"  Created ContentItem: {content_id}")

                # Auto-set page_count if not in metadata
                if not story.get("page_count") and pages:
                    print(
                        f"  (page_count not set in metadata; {len(pages)} pages will be uploaded)"
                    )

                for page in pages:
                    file_val = page.get("file", "")
                    page_path = (
                        Path(file_val)
                        if Path(file_val).is_absolute()
                        else (
                            (assets_root / file_val) if assets_root else Path(file_val)
                        )
                    )
                    if not page_path.exists():
                        print(f"  [WARN] Page file not found, skipping: {page_path}")
                        continue

                    result = await upload_page(
                        client=client,
                        base_url=base_url,
                        content_id=content_id,
                        page_path=page_path,
                        page_number=page.get("page_number", 1),
                        narration_text=page.get("narration_text"),
                        has_activity=bool(page.get("has_activity", False)),
                        asset_type=page.get("asset_type", "illustration"),
                    )
                    asset_id = result.get("id") or (result.get("data") or {}).get(
                        "id", "?"
                    )
                    print(f"    Page {page.get('page_number')}: asset {asset_id}")

            except httpx.HTTPStatusError as exc:
                print(
                    f"  [ERROR] HTTP {exc.response.status_code}: {exc.response.text[:200]}"
                )
            except Exception as exc:  # noqa: BLE001
                print(f"  [ERROR] {exc}")

    print("\nDone.")


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import story content assets into the Ecole Platform via the CMS API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manifest", type=Path, help="Path to JSON manifest file")
    source.add_argument(
        "--dir", type=Path, dest="stories_dir", help="Directory with story sub-folders"
    )

    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--email",
        default="admin@ecole.dz",
        help="Admin account email for authentication",
    )
    parser.add_argument(
        "--password", default="Admin1234!", help="Admin account password"
    )
    parser.add_argument(
        "--assets-root",
        type=Path,
        default=None,
        help="Root dir for resolving relative file paths in manifest",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate manifest without making API calls",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    if args.manifest:
        print(f"Loading manifest: {args.manifest}")
        stories = load_manifest(args.manifest)
        assets_root = args.assets_root or args.manifest.parent
    else:
        print(f"Discovering stories in: {args.stories_dir}")
        stories = discover_from_dir(args.stories_dir)
        assets_root = args.stories_dir

    if not stories:
        print("No stories found. Exiting.")
        sys.exit(0)

    if args.dry_run:
        token = "dry-run-token"
    else:
        print(f"Authenticating as {args.email}...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            token = await login(client, args.base_url, args.email, args.password)
        print("  Authenticated.")

    await import_stories(
        stories=stories,
        base_url=args.base_url,
        token=token,
        assets_root=assets_root,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    asyncio.run(main())
