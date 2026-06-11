"""Generate a draft quiz from a PDF+audio content item (Feature B).

Teacher-triggered: the teacher picks question types, count, and which sources to
merge (deterministic *templates* and/or the *AI* provider). Questions are built
from the content's per-page ``narration_text`` and written as a **draft** quiz
the teacher reviews and publishes.

Design notes:
- AI questions route through the existing pluggable provider
  (``create_ai_provider``) — mock by default, real Claude / open model when
  configured. No new AI infrastructure.
- No DB schema change: the per-question ``source`` ("ai" | "template") is
  returned in the API response for the review UI. Persisting it as a column is a
  clean follow-up once the Alembic heads are merged.
- Audio is handled by the players at runtime (existing ``question_media_path``
  if present, else TTS), so nothing audio-specific is needed here.

The pure helpers (``build_template_questions``, ``build_ai_messages``,
``parse_ai_questions``) are module-level and unit-testable without a database.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from sqlalchemy import select

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.core.unit_of_work import UnitOfWork
from app.models.lms import ContentItemAsset, QuestionType
from app.repositories.content_cms import CMSRepository
from app.repositories.lms_quiz import QuizRepository
from app.services.ai.provider_factory import create_ai_provider
from app.services.platform.audit import AuditService

logger = logging.getLogger(__name__)

# Types templates can build deterministically. AI may also produce MATCHING.
TEMPLATE_TYPES = {"MCQ", "TRUE_FALSE", "FILL_IN"}
ALLOWED_TYPES = {item.value for item in QuestionType}
DEFAULT_TYPES = ["MCQ", "TRUE_FALSE", "FILL_IN"]

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?؟。])\s+")
_LETTER_IDS = ["a", "b", "c", "d", "e", "f"]


def split_sentences(text: str, *, min_len: int = 20) -> list[str]:
    """Split narration into usable sentences (long enough to quiz on)."""
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(text or "") if p.strip()]
    return [p for p in parts if len(p) >= min_len]


def _normalize_types(types: list[str] | None) -> list[str]:
    if not types:
        return list(DEFAULT_TYPES)
    cleaned = [t.upper() for t in types if t and t.upper() in ALLOWED_TYPES]
    return cleaned or list(DEFAULT_TYPES)


def _longest_word(sentence: str) -> str | None:
    words = re.findall(r"[^\W\d_]{4,}", sentence, flags=re.UNICODE)
    if not words:
        return None
    return max(words, key=len)


_TEMPLATE_STEMS: dict[str, dict[str, str]] = {
    "tf": {"ar": "صح أم خطأ: ", "fr": "Vrai ou faux : ", "en": "True or false: "},
    "fill": {"ar": "أكمل: ", "fr": "Complète : ", "en": "Complete: "},
    "mcq": {
        "ar": "وفقًا للنص، أيُّ عبارة صحيحة؟",
        "fr": "D'après le texte, quelle affirmation est correcte ?",
        "en": "According to the text, which statement is correct?",
    },
    "tf_explain": {
        "ar": "هذه العبارة مأخوذة مباشرةً من النص.",
        "fr": "Cette affirmation provient directement du texte.",
        "en": "This statement comes straight from the text.",
    },
}


def _stem(key: str, language: str) -> str:
    table = _TEMPLATE_STEMS[key]
    return table.get(language, table["fr"])


def build_template_questions(
    text: str, types: list[str], count: int, language: str = "fr"
) -> list[dict[str, Any]]:
    """Deterministic, no-AI question generation from narration sentences."""
    sentences = split_sentences(text)
    if not sentences:
        return []
    wanted = [t for t in _normalize_types(types) if t in TEMPLATE_TYPES] or [
        "TRUE_FALSE"
    ]
    questions: list[dict[str, Any]] = []
    ti = 0
    si = 0
    guard = 0
    while len(questions) < count and guard < count * 4:
        guard += 1
        qtype = wanted[ti % len(wanted)]
        ti += 1
        sentence = sentences[si % len(sentences)]
        si += 1

        if qtype == "TRUE_FALSE":
            questions.append(
                {
                    "question_type": "TRUE_FALSE",
                    "question_text": f"{_stem('tf', language)}{sentence}",
                    "options": None,
                    "correct_answer": True,
                    "explanation": _stem("tf_explain", language),
                    "_source": "template",
                }
            )
        elif qtype == "FILL_IN":
            word = _longest_word(sentence)
            if not word:
                continue
            blanked = sentence.replace(word, "____", 1)
            questions.append(
                {
                    "question_type": "FILL_IN",
                    "question_text": f"{_stem('fill', language)}{blanked}",
                    "options": None,
                    "correct_answer": [word],
                    "explanation": None,
                    "_source": "template",
                }
            )
        elif qtype == "MCQ":
            distractors = [s for s in sentences if s != sentence][:3]
            if len(distractors) < 2:
                # Not enough material for a real MCQ → fall back to true/false.
                questions.append(
                    {
                        "question_type": "TRUE_FALSE",
                        "question_text": f"{_stem('tf', language)}{sentence}",
                        "options": None,
                        "correct_answer": True,
                        "explanation": None,
                        "_source": "template",
                    }
                )
                continue
            choices = [sentence, *distractors]
            options = [
                {"id": _LETTER_IDS[i], "text": choice}
                for i, choice in enumerate(choices)
            ]
            questions.append(
                {
                    "question_type": "MCQ",
                    "question_text": _stem("mcq", language),
                    "options": options,
                    "correct_answer": ["a"],  # the real sentence is first
                    "explanation": None,
                    "_source": "template",
                }
            )
    return questions[:count]


def build_ai_messages(
    text: str, types: list[str], count: int, language: str
) -> tuple[str, str]:
    """Build (system, prompt) asking the LLM for strict-JSON questions."""
    wanted = _normalize_types(types)
    system = (
        "You are an assessment generator for a Moroccan K-12 school platform. "
        "You write questions strictly grounded in the provided lesson text. "
        "Respond with STRICT JSON only — no prose, no markdown."
    )
    schema = (
        '[{"question_type": "MCQ|TRUE_FALSE|FILL_IN|MATCHING", '
        '"question_text": "string", '
        '"options": [{"id": "a", "text": "string"}]  // for MCQ only, '
        '"correct_answer": ["a"] | true | ["word"] | {"left": "right"}, '
        '"explanation": "string"}]'
    )
    prompt = (
        f"Language: {language}\n"
        f"Allowed question types: {', '.join(wanted)}\n"
        f"Number of questions: {count}\n"
        f"Return a JSON array following this shape:\n{schema}\n\n"
        f"Lesson text:\n{text[:4000]}"
    )
    return system, prompt


def _coerce_question(item: Any, allowed: set[str]) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    qtype = str(item.get("question_type") or "").upper()
    if qtype not in allowed:
        return None
    qtext = str(item.get("question_text") or "").strip()
    if not qtext:
        return None
    correct = item.get("correct_answer")
    if correct is None:
        return None
    options = item.get("options")
    if qtype == "MCQ" and not isinstance(options, list):
        return None
    return {
        "question_type": qtype,
        "question_text": qtext,
        "options": options if isinstance(options, (list, dict)) else None,
        "correct_answer": correct,
        "explanation": (
            str(item.get("explanation")).strip()
            if item.get("explanation") is not None
            else None
        ),
        "_source": "ai",
    }


def parse_ai_questions(
    raw: str, types: list[str], language: str
) -> list[dict[str, Any]]:
    """Parse the LLM's JSON output into validated question dicts (drop invalid)."""
    allowed = {t.upper() for t in _normalize_types(types)}
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if isinstance(data, dict):
        data = data.get("questions") or data.get("items") or []
    if not isinstance(data, list):
        return []
    out: list[dict[str, Any]] = []
    for item in data:
        coerced = _coerce_question(item, allowed)
        if coerced:
            out.append(coerced)
    return out


def to_question_payload(
    question: dict[str, Any], quiz_id: uuid.UUID, order: int
) -> dict[str, Any]:
    """Strip transient keys (_source) and shape a QuizQuestion row payload."""
    return {
        "quiz_id": quiz_id,
        "question_type": question["question_type"],
        "question_text": question["question_text"],
        "question_media_path": question.get("question_media_path"),
        "options": question.get("options"),
        "correct_answer": question["correct_answer"],
        "points": int(question.get("points", 1) or 1),
        "order": order,
        "explanation": question.get("explanation"),
        "source": question.get("_source"),
    }


class ContentQuizService:
    """Generate a draft quiz from a content item's narration text."""

    def __init__(self, db) -> None:
        self.db = db

    async def _load_narration(self, content_id: uuid.UUID) -> str:
        result = await self.db.execute(
            select(ContentItemAsset.narration_text, ContentItemAsset.page_number)
            .where(
                ContentItemAsset.content_item_id == content_id,
                ContentItemAsset.narration_text.isnot(None),
            )
            .order_by(ContentItemAsset.page_number)
        )
        texts = [row[0].strip() for row in result.all() if row[0] and row[0].strip()]
        return "\n".join(texts).strip()

    async def generate_from_content(
        self,
        *,
        content_id: uuid.UUID,
        body: Any,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict[str, Any]:
        cms = CMSRepository(self.db)
        content = await cms.get_content_item(content_id)
        if content is None:
            raise NotFoundError("Content not found", error_code="ERR-CONTENT-404")

        narration = await self._load_narration(content_id)
        if not narration:
            raise ValidationError(
                "This content has no narration text to build a quiz from.",
                error_code="ERR-QUIZ-NO-SOURCE",
            )

        types = _normalize_types(getattr(body, "question_types", None))
        count = max(1, int(getattr(body, "count", 5) or 5))
        sources = [
            s.lower() for s in (getattr(body, "sources", None) or ["template"])
        ]
        language = content.language or "fr"

        generated: list[dict[str, Any]] = []
        if "ai" in sources:
            try:
                provider = create_ai_provider(settings)
                system, prompt = build_ai_messages(narration, types, count, language)
                raw = await provider.complete(prompt, system, max_tokens=1200)
                generated.extend(parse_ai_questions(raw, types, language))
            except Exception:
                logger.exception("AI quiz generation failed, relying on templates")
        if "template" in sources or not generated:
            generated.extend(
                build_template_questions(narration, types, count, language)
            )

        questions = generated[:count]
        if not questions:
            raise ValidationError(
                "Could not generate any questions from this content.",
                error_code="ERR-QUIZ-EMPTY",
            )

        async with UnitOfWork(self.db) as uow:
            quiz_repo = QuizRepository(uow.session)
            audit = AuditService(uow.session)
            quiz = await quiz_repo.create_quiz(
                school_id=auth.school_id,
                created_by=auth.user_id,
                title=getattr(body, "title", None) or f"Quiz — {content.title}",
                description=(
                    getattr(body, "description", None)
                    or f"Généré depuis le contenu : {content.title}"
                ),
                subject=content.subject,
                level_band=content.level_band,
                difficulty=getattr(body, "difficulty", None),
                time_limit_minutes=getattr(body, "time_limit_minutes", None),
                max_attempts=int(getattr(body, "max_attempts", 1) or 1),
                shuffle_questions=bool(getattr(body, "shuffle_questions", False)),
                status="draft",
                source_content_id=content_id,
                language=language,
            )
            payloads = [
                to_question_payload(q, quiz.id, index)
                for index, q in enumerate(questions)
            ]
            await quiz_repo.create_quiz_questions(payloads)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CONTENT_QUIZ_GENERATED",
                outcome="success",
                target_type="quiz",
                target_id=quiz.id,
                entity_after={
                    "source_content_id": str(content_id),
                    "question_count": len(payloads),
                    "sources": sources,
                    "types": types,
                },
                ip_address=ip_address,
            )
            await uow.commit()
            quiz_id = quiz.id
            quiz_title = quiz.title

        return {
            "quiz_id": str(quiz_id),
            "title": quiz_title,
            "status": "draft",
            "language": language,
            "source_content_id": str(content_id),
            "question_count": len(questions),
            "questions": [
                {
                    "order": index,
                    "question_type": q["question_type"],
                    "question_text": q["question_text"],
                    "source": q.get("_source", "template"),
                }
                for index, q in enumerate(questions)
            ],
        }
