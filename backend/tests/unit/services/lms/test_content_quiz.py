"""Unit tests for the content→quiz pure generation helpers (Feature B).

These cover the database-free building blocks: sentence splitting, deterministic
template generation, and robust parsing of the AI provider's JSON output.
"""

from __future__ import annotations

import json

from app.services.lms.content_quiz import (
    build_template_questions,
    parse_ai_questions,
    split_sentences,
    to_question_payload,
)

SAMPLE = (
    "Le chat est un animal domestique. "
    "Le chien aime jouer dans le jardin. "
    "Les oiseaux volent haut dans le ciel bleu. "
    "La girafe possède un très long cou."
)


class TestSplitSentences:
    def test_splits_and_filters_short(self) -> None:
        sentences = split_sentences(SAMPLE)
        assert len(sentences) == 4
        assert all(len(s) >= 20 for s in sentences)

    def test_empty_text_returns_empty(self) -> None:
        assert split_sentences("") == []
        assert split_sentences(None) == []  # type: ignore[arg-type]


class TestTemplateGeneration:
    def test_generates_requested_count(self) -> None:
        questions = build_template_questions(
            SAMPLE, ["MCQ", "TRUE_FALSE", "FILL_IN"], 5
        )
        assert len(questions) == 5
        assert all("correct_answer" in q for q in questions)
        assert all(q["_source"] == "template" for q in questions)

    def test_mcq_has_four_options_and_first_is_correct(self) -> None:
        questions = build_template_questions(SAMPLE, ["MCQ"], 1)
        mcq = questions[0]
        assert mcq["question_type"] == "MCQ"
        assert len(mcq["options"]) == 4
        assert mcq["correct_answer"] == ["a"]

    def test_true_false_correct_answer_is_bool(self) -> None:
        questions = build_template_questions(SAMPLE, ["TRUE_FALSE"], 1)
        assert questions[0]["correct_answer"] is True

    def test_fill_in_blanks_a_word(self) -> None:
        questions = build_template_questions(SAMPLE, ["FILL_IN"], 1)
        q = questions[0]
        assert q["question_type"] == "FILL_IN"
        assert "____" in q["question_text"]
        assert isinstance(q["correct_answer"], list) and q["correct_answer"]

    def test_no_sentences_returns_empty(self) -> None:
        assert build_template_questions("short", ["MCQ"], 5) == []


class TestParseAiQuestions:
    def test_drops_invalid_and_keeps_valid(self) -> None:
        raw = json.dumps(
            [
                {
                    "question_type": "TRUE_FALSE",
                    "question_text": "Le chat est domestique ?",
                    "correct_answer": True,
                },
                {"question_type": "BOGUS", "question_text": "x", "correct_answer": 1},
                {
                    "question_type": "MCQ",
                    "question_text": "Choisis :",
                    "options": [{"id": "a", "text": "x"}],
                    "correct_answer": ["a"],
                },
                {"question_type": "MCQ", "question_text": "no options"},  # invalid
            ]
        )
        parsed = parse_ai_questions(raw, ["MCQ", "TRUE_FALSE", "FILL_IN"], "fr")
        assert len(parsed) == 2
        assert all(p["_source"] == "ai" for p in parsed)

    def test_accepts_object_with_questions_key(self) -> None:
        raw = json.dumps(
            {
                "questions": [
                    {
                        "question_type": "TRUE_FALSE",
                        "question_text": "Vrai ?",
                        "correct_answer": False,
                    }
                ]
            }
        )
        parsed = parse_ai_questions(raw, ["TRUE_FALSE"], "fr")
        assert len(parsed) == 1

    def test_invalid_json_returns_empty(self) -> None:
        assert parse_ai_questions("not json {", ["MCQ"], "fr") == []


class TestPayload:
    def test_strips_transient_source_key(self) -> None:
        import uuid

        q = build_template_questions(SAMPLE, ["TRUE_FALSE"], 1)[0]
        quiz_id = uuid.uuid4()
        payload = to_question_payload(q, quiz_id, 0)
        assert "_source" not in payload
        assert payload["quiz_id"] == quiz_id
        assert payload["order"] == 0
        assert payload["question_type"] == "TRUE_FALSE"
