"""Import extracted friend educational content into the LMS content library.

Run with:
    cd backend && python scripts/seed_friend_content.py
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import mimetypes
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.core.database import async_session
from app.models.iam import Membership, User
from app.models.lms import ContentItem, ContentItemAsset, Quiz, QuizQuestion


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEV_ROOT = BACKEND_ROOT.parent
DEFAULT_REFERENCE_ROOT = (
    Path("/ecole-platform-reference")
    if not DEV_ROOT.name
    else DEV_ROOT.with_name("ecole-platform-reference")
)
REFERENCE_ROOT = Path(
    os.getenv("FRIEND_CONTENT_REFERENCE_ROOT", str(DEFAULT_REFERENCE_ROOT))
)
ASSETS_ROOT = Path(
    os.getenv(
        "FRIEND_CONTENT_ASSETS_ROOT",
        str(REFERENCE_ROOT / "extraction" / "assets"),
    )
)
MANIFEST_PATH = ASSETS_ROOT / "config" / "stories_manifest.json"

UPLOAD_ROOT = Path(settings.upload_dir)
if not UPLOAD_ROOT.is_absolute():
    UPLOAD_ROOT = (BACKEND_ROOT / UPLOAD_ROOT).resolve()

UUID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "ecole-platform/friend-content")
STATUS_PUBLISHED = "published"
ORIGIN_PLATFORM = "PLATFORM"
SUBJECT_ARABIC = "arabic"
SUBJECT_ART = "art"
LANGUAGE_AR = "ar"

PREFERRED_CREATOR_ROLES = ("CONTENT_MGR", "SUP", "ADM", "TCH")

STORY_TITLE_FALLBACKS = {
    "intro": "مقدمة عالم سامي",
    "alif": "حرف الألف",
    "bae": "حرف الباء",
    "zay": "حرف الزاي",
}

PDF_TITLES = {
    "intro": "مغامرة سامي في عالم الحروف - نسخة PDF",
    "alif": "قصة حرف الألف - نسخة PDF",
    "bae": "قصة حرف الباء - نسخة PDF",
    "zay": "قصة حرف الزاي - نسخة PDF",
    "coloring_animal_letters": "دفتر تلوين الحروف والحيوانات",
}

VIDEO_TITLES = {
    "intro_video": "فيديو مغامرة سامي في عالم الحروف",
    "zay_video": "فيديو قصة حرف الزاي",
}

VIDEO_DESCRIPTIONS = {
    "intro_video": "فيديو قصير مرافق لقصة مغامرة سامي في عالم الحروف.",
    "zay_video": "فيديو تعليمي مرافق لقصة حرف الزاي.",
}


@dataclass(slots=True)
class ImportStats:
    stories: int = 0
    coloring_pages: int = 0
    audio_files: int = 0
    pdfs: int = 0
    videos: int = 0
    mascot_images: int = 0
    quizzes: int = 0
    warnings: int = 0


def _content_uuid(*parts: object) -> uuid.UUID:
    key = "::".join(str(part) for part in parts)
    return uuid.uuid5(UUID_NAMESPACE, key)


def _safe_name(filename: str) -> str:
    cleaned = re.sub(r"\s+", "_", filename.strip())
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")
    return cleaned or "asset"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _guess_mime_type(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    if mime_type:
        return mime_type
    extension = path.suffix.lower()
    if extension == ".mp3":
        return "audio/mpeg"
    if extension == ".mp4":
        return "video/mp4"
    if extension == ".pdf":
        return "application/pdf"
    if extension == ".png":
        return "image/png"
    if extension in {".jpg", ".jpeg"}:
        return "image/jpeg"
    return "application/octet-stream"


def _warn(stats: ImportStats, message: str) -> None:
    stats.warnings += 1
    print(f"WARNING: {message}")


def _parse_target_age(raw: object) -> tuple[int | None, int | None]:
    if raw is None:
        return None, None
    if isinstance(raw, (list, tuple)):
        values = [int(value) for value in raw[:2]]
        if len(values) == 2:
            return values[0], values[1]
        if len(values) == 1:
            return values[0], values[0]
        return None, None

    values = [int(value) for value in re.findall(r"\d+", str(raw))]
    if len(values) >= 2:
        return values[0], values[1]
    if len(values) == 1:
        return values[0], values[0]
    return None, None


def _story_title(story: dict) -> str:
    return str(story.get("title") or "").strip() or STORY_TITLE_FALLBACKS.get(
        str(story["id"]), str(story["id"])
    )


def _story_description(story: dict) -> str:
    existing = str(story.get("description") or "").strip()
    if existing:
        return existing
    letter = str(story.get("letter") or "").strip()
    if letter:
        return f"قصة تعليمية تفاعلية لمساعدة الطفل على تعلم حرف {letter} بطريقة ممتعة."
    return f"قصة تعليمية تفاعلية ضمن مكتبة سامي التعليمية بعنوان {_story_title(story)}."


def _relative_asset_path(raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    normalized = str(raw_path).strip().replace("\\", "/")
    if normalized.startswith("assets/"):
        normalized = normalized[len("assets/") :]
    candidate = ASSETS_ROOT / normalized
    if candidate.exists():
        return candidate
    return None


def _resolve_reference_path(
    raw_path: str | None,
    *,
    fallback_dirs: tuple[str, ...] = (),
) -> Path | None:
    candidate = _relative_asset_path(raw_path)
    if candidate is not None:
        return candidate

    if not raw_path:
        return None

    basename = Path(raw_path).name
    for directory in fallback_dirs:
        fallback = ASSETS_ROOT / directory / basename
        if fallback.exists():
            return fallback

    matches = list(ASSETS_ROOT.rglob(basename))
    if len(matches) == 1:
        return matches[0]
    if matches:
        return sorted(matches)[0]
    return None


def _resolve_page_path(story_id: str, page_number: int, extension: str) -> Path | None:
    primary = (
        ASSETS_ROOT / "stories" / story_id / "pages" / f"page_{page_number}.{extension}"
    )
    if primary.exists():
        return primary

    candidates = sorted(
        (ASSETS_ROOT / "stories" / story_id / "pages").glob(f"page_{page_number}.*")
    )
    if candidates:
        return candidates[0]
    return None


def _copy_to_uploads(source: Path, relative_path: str) -> tuple[str, int, str]:
    target = UPLOAD_ROOT / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)

    source_checksum = _sha256_file(source)
    if target.exists():
        same_size = target.stat().st_size == source.stat().st_size
        if same_size and _sha256_file(target) == source_checksum:
            return relative_path, source.stat().st_size, source_checksum

    shutil.copy2(source, target)
    return relative_path, source.stat().st_size, source_checksum


def _parse_page_number_from_name(filename: str) -> int | None:
    match = re.search(r"page[\s_]*(\d+)", filename, flags=re.IGNORECASE)
    if match is None:
        return None
    return int(match.group(1))


async def _pick_creator_user_id(session: AsyncSession) -> uuid.UUID | None:
    for role_code in PREFERRED_CREATOR_ROLES:
        result = await session.execute(
            select(Membership.user_id)
            .join(User, User.id == Membership.user_id)
            .where(
                Membership.role_code == role_code,
                Membership.status == "active",
                User.status == "active",
            )
            .limit(1)
        )
        user_id = result.scalar_one_or_none()
        if user_id is not None:
            return user_id

    result = await session.execute(
        select(User.id)
        .where(User.status == "active")
        .order_by(User.created_at)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _upsert_content_item(
    session: AsyncSession,
    *,
    content_id: uuid.UUID,
    title: str,
    content_type: str,
    subject: str | None,
    language: str | None,
    description: str | None,
    created_by: uuid.UUID | None,
    page_count: int | None = None,
    letter: str | None = None,
    target_age_min: int | None = None,
    target_age_max: int | None = None,
    theme_color: str | None = None,
    thumbnail_path: str | None = None,
) -> tuple[ContentItem, bool]:
    item = await session.get(ContentItem, content_id)
    created = False
    if item is None:
        result = await session.execute(
            select(ContentItem)
            .where(
                ContentItem.school_id.is_(None),
                ContentItem.content_type == content_type,
                ContentItem.title == title,
            )
            .limit(1)
        )
        item = result.scalar_one_or_none()

    if item is None:
        item = ContentItem(id=content_id)
        session.add(item)
        created = True

    item.school_id = None
    item.title = title
    item.content_type = content_type
    item.subject = subject
    item.language = language
    item.status = STATUS_PUBLISHED
    item.origin = ORIGIN_PLATFORM
    item.created_by = created_by
    item.description = description
    item.page_count = page_count
    item.letter = letter
    item.target_age_min = target_age_min
    item.target_age_max = target_age_max
    item.theme_color = theme_color
    item.thumbnail_path = thumbnail_path

    await session.flush()
    return item, created


async def _upsert_asset(
    session: AsyncSession,
    *,
    asset_id: uuid.UUID,
    content_item_id: uuid.UUID,
    file_path: str,
    checksum: str,
    mime_type: str,
    file_size: int,
    page_number: int | None,
    has_activity: bool,
    asset_type: str,
    narration_text: str | None = None,
) -> tuple[ContentItemAsset, bool]:
    asset = await session.get(ContentItemAsset, asset_id)
    created = False
    if asset is None:
        result = await session.execute(
            select(ContentItemAsset)
            .where(
                ContentItemAsset.content_item_id == content_item_id,
                ContentItemAsset.file_path == file_path,
            )
            .limit(1)
        )
        asset = result.scalar_one_or_none()

    if asset is None:
        asset = ContentItemAsset(id=asset_id, content_item_id=content_item_id)
        session.add(asset)
        created = True

    asset.content_item_id = content_item_id
    asset.file_path = file_path
    asset.checksum = checksum
    asset.mime_type = mime_type
    asset.file_size = file_size
    asset.page_number = page_number
    asset.narration_text = narration_text
    asset.has_activity = has_activity
    asset.asset_type = asset_type

    await session.flush()
    return asset, created


async def _upsert_quiz(
    session: AsyncSession,
    *,
    quiz_id: uuid.UUID,
    created_by: uuid.UUID,
    title: str,
    description: str,
    subject: str,
    difficulty: str,
) -> tuple[Quiz, bool]:
    quiz = await session.get(Quiz, quiz_id)
    created = False
    if quiz is None:
        result = await session.execute(
            select(Quiz)
            .where(
                Quiz.school_id.is_(None),
                Quiz.title == title,
            )
            .limit(1)
        )
        quiz = result.scalar_one_or_none()

    if quiz is None:
        quiz = Quiz(id=quiz_id)
        session.add(quiz)
        created = True

    quiz.school_id = None
    quiz.created_by = created_by
    quiz.title = title
    quiz.description = description
    quiz.subject = subject
    quiz.level_band = "primaire"
    quiz.difficulty = difficulty
    quiz.time_limit_minutes = 5
    quiz.max_attempts = 3
    quiz.shuffle_questions = False
    quiz.status = STATUS_PUBLISHED

    await session.flush()
    return quiz, created


async def _upsert_quiz_question(
    session: AsyncSession,
    *,
    question_id: uuid.UUID,
    quiz_id: uuid.UUID,
    question_type: str,
    question_text: str,
    options: list[dict[str, str]] | None,
    correct_answer: list[str],
    explanation: str | None = None,
) -> tuple[QuizQuestion, bool]:
    question = await session.get(QuizQuestion, question_id)
    created = False
    if question is None:
        result = await session.execute(
            select(QuizQuestion)
            .where(
                QuizQuestion.quiz_id == quiz_id,
                QuizQuestion.order == 0,
            )
            .limit(1)
        )
        question = result.scalar_one_or_none()

    if question is None:
        question = QuizQuestion(id=question_id, quiz_id=quiz_id)
        session.add(question)
        created = True

    question.quiz_id = quiz_id
    question.question_type = question_type
    question.question_text = question_text
    question.question_media_path = None
    question.options = options
    question.correct_answer = correct_answer
    question.points = 1
    question.order = 0
    question.explanation = explanation

    await session.flush()
    return question, created


async def _import_stories(
    session: AsyncSession,
    *,
    creator_user_id: uuid.UUID | None,
    stats: ImportStats,
) -> dict[str, ContentItem]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")

    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    stories = payload.get("stories", [])
    story_items: dict[str, ContentItem] = {}

    for story in stories:
        story_id = str(story["id"])
        title = _story_title(story)
        description = _story_description(story)
        target_age_min, target_age_max = _parse_target_age(story.get("targetAge"))
        page_count = int(story.get("pageCount") or 0)
        activities = list(story.get("activities") or [])
        activities_by_page = {
            int(activity["page"]): []
            for activity in activities
            if activity.get("page") is not None
        }
        for activity in activities:
            page_number = int(activity["page"])
            activities_by_page.setdefault(page_number, []).append(activity)

        cover_source = _resolve_reference_path(
            story.get("coverImage"),
            fallback_dirs=("images/story-covers", "images"),
        )
        cover_relative_path = None
        if cover_source is not None:
            cover_relative_path = (
                f"content/stories/{story_id}/cover{cover_source.suffix.lower()}"
            )
            cover_relative_path, cover_size, cover_checksum = _copy_to_uploads(
                cover_source,
                cover_relative_path,
            )
        else:
            cover_size = 0
            cover_checksum = ""
            _warn(stats, f"Missing cover image for story '{story_id}'")

        content_item, created = await _upsert_content_item(
            session,
            content_id=_content_uuid("story", story_id),
            title=title,
            content_type="story",
            subject=SUBJECT_ARABIC,
            language=LANGUAGE_AR,
            description=description,
            created_by=creator_user_id,
            page_count=page_count,
            letter=str(story.get("letter") or "").strip() or None,
            target_age_min=target_age_min,
            target_age_max=target_age_max,
            theme_color=str(story.get("colorHex") or "").strip() or None,
            thumbnail_path=cover_relative_path,
        )
        story_items[story_id] = content_item

        if cover_relative_path is not None and cover_source is not None:
            await _upsert_asset(
                session,
                asset_id=_content_uuid("story-cover", story_id),
                content_item_id=content_item.id,
                file_path=cover_relative_path,
                checksum=cover_checksum,
                mime_type=_guess_mime_type(cover_source),
                file_size=cover_size,
                page_number=None,
                has_activity=False,
                asset_type="cover",
            )

        for page_number in range(1, page_count + 1):
            page_source = _resolve_page_path(
                story_id,
                page_number,
                str(story.get("ext") or "png").lstrip("."),
            )
            if page_source is None:
                _warn(
                    stats,
                    f"Missing page image for story '{story_id}' page {page_number}",
                )
                continue

            relative_path = (
                f"content/stories/{story_id}/pages/page_{page_number}"
                f"{page_source.suffix.lower()}"
            )
            relative_path, size_bytes, checksum = _copy_to_uploads(
                page_source,
                relative_path,
            )
            await _upsert_asset(
                session,
                asset_id=_content_uuid("story-page", story_id, page_number),
                content_item_id=content_item.id,
                file_path=relative_path,
                checksum=checksum,
                mime_type=_guess_mime_type(page_source),
                file_size=size_bytes,
                page_number=page_number,
                has_activity=bool(activities_by_page.get(page_number)),
                asset_type="page_image",
            )

        activity_count = 0
        for index, activity in enumerate(activities):
            if creator_user_id is None:
                _warn(
                    stats,
                    f"Skipping activity import for story '{story_id}' because no creator user exists",
                )
                break

            page_number = int(activity["page"])
            options_values = list(activity.get("options") or [])
            target_value = str(activity.get("target") or "").strip()
            options_payload = None
            correct_answer = [target_value] if target_value else []
            question_type = "FILL_IN"

            if options_values:
                options_payload = [
                    {"id": chr(ord("a") + option_index), "text": str(option_value)}
                    for option_index, option_value in enumerate(options_values)
                ]
                matching = [
                    option["id"]
                    for option in options_payload
                    if option["text"] == target_value
                ]
                correct_answer = matching or correct_answer
                question_type = "MCQ"

            quiz_title = f"نشاط {title} - الصفحة {page_number}"
            quiz_description = (
                f"نشاط تفاعلي مستخرج من القصة '{title}' في الصفحة {page_number}."
            )
            quiz, quiz_created = await _upsert_quiz(
                session,
                quiz_id=_content_uuid("story-quiz", story_id, page_number, index),
                created_by=creator_user_id,
                title=quiz_title,
                description=quiz_description,
                subject=SUBJECT_ARABIC,
                difficulty="EASY",
            )
            _, question_created = await _upsert_quiz_question(
                session,
                question_id=_content_uuid(
                    "story-quiz-question",
                    story_id,
                    page_number,
                    index,
                ),
                quiz_id=quiz.id,
                question_type=question_type,
                question_text=str(activity.get("prompt") or "نشاط تفاعلي"),
                options=options_payload,
                correct_answer=correct_answer,
                explanation=(
                    f"الإجابة الصحيحة هي: {target_value}" if target_value else None
                ),
            )
            if quiz_created or question_created:
                stats.quizzes += int(quiz_created)
            activity_count += 1

        stats.stories += 1
        action = "Created" if created else "Existing"
        print(
            f"{action} story: {title} ({page_count} pages, {activity_count} activities)"
        )

    return story_items


async def _import_coloring_books(
    session: AsyncSession,
    *,
    creator_user_id: uuid.UUID | None,
    stats: ImportStats,
) -> None:
    books = [
        {
            "slug": "animals",
            "title": "حيوانات للتلوين",
            "description": "دفتر تلوين يضم صور حيوانات بسيطة ومناسبة للأطفال.",
            "page_count": 28,
            "theme_color": "#F4B400",
            "target_age": (4, 7),
            "source_dir": ASSETS_ROOT / "coloring-books" / "animals",
            "cover_candidates": (
                ASSETS_ROOT / "coloring-books" / "animals" / "cover.png",
                ASSETS_ROOT
                / "images"
                / "coloring-covers"
                / "coloring_animal_cover.png",
            ),
        },
        {
            "slug": "fruits-vegetables",
            "title": "فواكه وخضروات للتلوين",
            "description": "دفتر تلوين يضم صور فواكه وخضروات مناسبة للتعلم المبكر.",
            "page_count": 5,
            "theme_color": "#43A047",
            "target_age": (4, 7),
            "source_dir": ASSETS_ROOT / "coloring-books" / "fruits-vegetables",
            "cover_candidates": (
                ASSETS_ROOT / "images" / "coloring-covers" / "fruits_veg_cover.png",
            ),
        },
    ]

    for book in books:
        cover_source = next(
            (candidate for candidate in book["cover_candidates"] if candidate.exists()),
            None,
        )
        cover_relative_path = None
        if cover_source is not None:
            cover_relative_path = (
                f"content/coloring/{book['slug']}/cover{cover_source.suffix.lower()}"
            )
            cover_relative_path, cover_size, cover_checksum = _copy_to_uploads(
                cover_source,
                cover_relative_path,
            )
        else:
            cover_size = 0
            cover_checksum = ""
            _warn(stats, f"Missing coloring cover for '{book['slug']}'")

        content_item, created = await _upsert_content_item(
            session,
            content_id=_content_uuid("coloring-book", book["slug"]),
            title=book["title"],
            content_type="coloring_book",
            subject=SUBJECT_ART,
            language=LANGUAGE_AR,
            description=book["description"],
            created_by=creator_user_id,
            page_count=book["page_count"],
            target_age_min=book["target_age"][0],
            target_age_max=book["target_age"][1],
            theme_color=book["theme_color"],
            thumbnail_path=cover_relative_path,
        )

        if cover_relative_path is not None and cover_source is not None:
            await _upsert_asset(
                session,
                asset_id=_content_uuid("coloring-cover", book["slug"]),
                content_item_id=content_item.id,
                file_path=cover_relative_path,
                checksum=cover_checksum,
                mime_type=_guess_mime_type(cover_source),
                file_size=cover_size,
                page_number=None,
                has_activity=False,
                asset_type="cover",
            )

        imported_pages = 0
        for page_number in range(1, int(book["page_count"]) + 1):
            page_source = book["source_dir"] / f"page_{page_number}.png"
            if not page_source.exists():
                _warn(
                    stats,
                    f"Missing coloring page for '{book['slug']}' page {page_number}",
                )
                continue

            relative_path = f"content/coloring/{book['slug']}/page_{page_number}.png"
            relative_path, size_bytes, checksum = _copy_to_uploads(
                page_source,
                relative_path,
            )
            await _upsert_asset(
                session,
                asset_id=_content_uuid("coloring-page", book["slug"], page_number),
                content_item_id=content_item.id,
                file_path=relative_path,
                checksum=checksum,
                mime_type="image/png",
                file_size=size_bytes,
                page_number=page_number,
                has_activity=False,
                asset_type="coloring_page",
            )
            imported_pages += 1

        stats.coloring_pages += imported_pages
        action = "Created" if created else "Existing"
        print(f"{action} coloring book: {book['title']} ({imported_pages} pages)")


async def _import_story_audio(
    session: AsyncSession,
    *,
    story_items: dict[str, ContentItem],
    stats: ImportStats,
) -> None:
    narration_root = ASSETS_ROOT / "audio" / "narration"
    if not narration_root.exists():
        _warn(stats, "Narration audio directory not found")
        return

    imported_for_story: dict[str, int] = {}
    for source in sorted(path for path in narration_root.rglob("*") if path.is_file()):
        story_key = source.parent.name.replace("story-", "").replace("story_", "")
        content_item = story_items.get(story_key)
        if content_item is None:
            _warn(stats, f"Skipping narration audio without matching story: {source}")
            continue

        page_number = _parse_page_number_from_name(source.name)
        relative_path = f"content/audio/{story_key}/{_safe_name(source.name)}"
        relative_path, size_bytes, checksum = _copy_to_uploads(source, relative_path)
        await _upsert_asset(
            session,
            asset_id=_content_uuid("story-audio", story_key, relative_path),
            content_item_id=content_item.id,
            file_path=relative_path,
            checksum=checksum,
            mime_type=_guess_mime_type(source),
            file_size=size_bytes,
            page_number=page_number,
            has_activity=False,
            asset_type="audio_narration",
        )
        imported_for_story[story_key] = imported_for_story.get(story_key, 0) + 1
        stats.audio_files += 1

    for story_key, count in imported_for_story.items():
        print(f"Imported narration audio: {story_key} ({count} files)")


async def _import_mascot_assets(
    session: AsyncSession,
    *,
    creator_user_id: uuid.UUID | None,
    stats: ImportStats,
) -> None:
    mascot_dir = ASSETS_ROOT / "images" / "mascots"
    if not mascot_dir.exists():
        _warn(stats, "Mascot image directory not found")
        return

    sources = sorted(path for path in mascot_dir.iterdir() if path.is_file())
    if not sources:
        _warn(stats, "No mascot images found")
        return

    for source in sources:
        relative_path = f"content/mascot/{_safe_name(source.name)}"
        relative_path, size_bytes, checksum = _copy_to_uploads(source, relative_path)
        mascot_stem = source.stem.replace("_", " ").strip()
        title = f"أصل سامي - {mascot_stem}"
        description = f"صورة أصلية لشخصية سامي ({source.name})."
        content_item, created = await _upsert_content_item(
            session,
            content_id=_content_uuid("mascot-asset", source.name),
            title=title,
            content_type="mascot_asset",
            subject="branding",
            language=LANGUAGE_AR,
            description=description,
            created_by=creator_user_id,
            page_count=1,
            thumbnail_path=relative_path,
            theme_color="#00ACC1",
        )
        await _upsert_asset(
            session,
            asset_id=_content_uuid("mascot-image", source.name),
            content_item_id=content_item.id,
            file_path=relative_path,
            checksum=checksum,
            mime_type=_guess_mime_type(source),
            file_size=size_bytes,
            page_number=None,
            has_activity=False,
            asset_type="mascot_image",
        )
        stats.mascot_images += 1
        action = "Created" if created else "Existing"
        print(f"{action} mascot asset: {title}")


async def _import_pdfs(
    session: AsyncSession,
    *,
    creator_user_id: uuid.UUID | None,
    stats: ImportStats,
) -> None:
    pdf_dir = ASSETS_ROOT / "pdfs"
    if not pdf_dir.exists():
        _warn(stats, "PDF directory not found")
        return

    for source in sorted(pdf_dir.glob("*.pdf")):
        stem = source.stem
        title = PDF_TITLES.get(stem, stem.replace("_", " ").strip())
        description = f"ملف PDF تعليمي بعنوان {title}."
        relative_path = f"content/pdfs/{_safe_name(source.name)}"
        relative_path, size_bytes, checksum = _copy_to_uploads(source, relative_path)
        content_item, created = await _upsert_content_item(
            session,
            content_id=_content_uuid("pdf", stem),
            title=title,
            content_type="pdf",
            subject=SUBJECT_ARABIC,
            language=LANGUAGE_AR,
            description=description,
            created_by=creator_user_id,
        )
        await _upsert_asset(
            session,
            asset_id=_content_uuid("pdf-asset", stem),
            content_item_id=content_item.id,
            file_path=relative_path,
            checksum=checksum,
            mime_type="application/pdf",
            file_size=size_bytes,
            page_number=None,
            has_activity=False,
            asset_type="pdf_document",
        )
        stats.pdfs += 1
        action = "Created" if created else "Existing"
        print(f"{action} PDF content: {title}")


async def _import_videos(
    session: AsyncSession,
    *,
    creator_user_id: uuid.UUID | None,
    stats: ImportStats,
) -> None:
    video_dir = ASSETS_ROOT / "videos"
    if not video_dir.exists():
        _warn(stats, "Video directory not found")
        return

    for source in sorted(path for path in video_dir.iterdir() if path.is_file()):
        stem = source.stem
        title = VIDEO_TITLES.get(stem, stem.replace("_", " ").strip())
        description = VIDEO_DESCRIPTIONS.get(
            stem,
            f"فيديو تعليمي بعنوان {title}.",
        )
        relative_path = f"content/videos/{_safe_name(source.name)}"
        relative_path, size_bytes, checksum = _copy_to_uploads(source, relative_path)
        content_item, created = await _upsert_content_item(
            session,
            content_id=_content_uuid("video", stem),
            title=title,
            content_type="video",
            subject=SUBJECT_ARABIC,
            language=LANGUAGE_AR,
            description=description,
            created_by=creator_user_id,
        )
        await _upsert_asset(
            session,
            asset_id=_content_uuid("video-asset", stem),
            content_item_id=content_item.id,
            file_path=relative_path,
            checksum=checksum,
            mime_type=_guess_mime_type(source),
            file_size=size_bytes,
            page_number=None,
            has_activity=False,
            asset_type="video_file",
        )
        stats.videos += 1
        action = "Created" if created else "Existing"
        print(f"{action} video content: {title}")


async def seed_friend_content() -> ImportStats:
    stats = ImportStats()

    if not ASSETS_ROOT.exists():
        raise FileNotFoundError(f"Friend asset directory not found: {ASSETS_ROOT}")

    async with async_session() as session:
        creator_user_id = await _pick_creator_user_id(session)
        if creator_user_id is None:
            print(
                "No active creator user found. Content will import without created_by, "
                "and quiz creation will be skipped."
            )

        story_items = await _import_stories(
            session,
            creator_user_id=creator_user_id,
            stats=stats,
        )
        await _import_coloring_books(
            session,
            creator_user_id=creator_user_id,
            stats=stats,
        )
        await _import_story_audio(
            session,
            story_items=story_items,
            stats=stats,
        )
        await _import_mascot_assets(
            session,
            creator_user_id=creator_user_id,
            stats=stats,
        )
        await _import_pdfs(
            session,
            creator_user_id=creator_user_id,
            stats=stats,
        )
        await _import_videos(
            session,
            creator_user_id=creator_user_id,
            stats=stats,
        )
        await session.commit()

    return stats


def _generate_friend_report(stats: ImportStats) -> None:
    """Generate a markdown report of imported friend content."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = f"""# Friend Content Seed Report — Generated {now}

> Auto-generated by `make seed-friend-content`. Do not edit manually.

## Imported Content

| Type | Count |
|------|-------|
| Stories (interactive) | {stats.stories} |
| Coloring pages | {stats.coloring_pages} |
| Audio narration files | {stats.audio_files} |
| PDF documents | {stats.pdfs} |
| Videos | {stats.videos} |
| Mascot images | {stats.mascot_images} |
| Quizzes (MCQ) | {stats.quizzes} |

## Content Details

### Stories (Sami character — Arabic letter learning)
- Introduction: مغامرة سامي في عالم الحروف
- Alif: حرف الألف
- Bae: حرف الباء
- Zay: حرف الزاي

### PDFs
- Story PDF versions (intro, alif, bae, zay)
- Coloring book: دفتر تلوين الحروف والحيوانات

### Videos
- مغامرة سامي في عالم الحروف (intro video)
- قصة حرف الزاي (zay video)

## Warnings: {stats.warnings}

*All content is Arabic-language, targeting maternelle/CP level.*
"""
    report_path = Path(__file__).resolve().parents[1] / "seed-friend-report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"  Report generated: {report_path}")


async def main() -> None:
    stats = await seed_friend_content()
    print(
        "Imported: "
        f"{stats.stories} stories, "
        f"{stats.coloring_pages} coloring pages, "
        f"{stats.audio_files} audio files, "
        f"{stats.pdfs} PDFs, "
        f"{stats.videos} videos"
    )
    print(
        "Extras: "
        f"{stats.mascot_images} mascot images, "
        f"{stats.quizzes} quizzes, "
        f"{stats.warnings} warnings"
    )
    _generate_friend_report(stats)


if __name__ == "__main__":
    asyncio.run(main())
