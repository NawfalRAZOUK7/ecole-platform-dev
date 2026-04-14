"""Game configuration factories."""

from __future__ import annotations

import uuid

import factory

from app.models.games import GameConfig
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.school import SchoolFactory


def _default_config(game_type: str) -> dict:
    if game_type == "sorting":
        return {
            "categories": [
                {"name": "حروف", "items": ["أ", "ب"]},
                {"name": "أرقام", "items": ["١", "٢"]},
            ]
        }
    if game_type == "vocabulary_cards":
        return {
            "cards": [
                {
                    "word_ar": "أرنب",
                    "word_fr": "Lapin",
                    "image_url": "https://cdn.example.com/lapin.png",
                    "audio_url": "https://cdn.example.com/lapin.mp3",
                }
            ]
        }
    return {
        "pairs": [
            {
                "front": "أ",
                "back": "أرنب",
                "image_url": "https://cdn.example.com/alif.png",
            },
            {
                "front": "ب",
                "back": "بطة",
                "image_url": "https://cdn.example.com/baa.png",
            },
        ],
        "grid_cols": 2,
        "grid_rows": 2,
        "time_limit_seconds": 60,
    }


class GameConfigFactory(AsyncSQLAlchemyFactory):
    """Factory for mobile game configuration rows."""

    class Meta:
        model = GameConfig
        exclude = ("school",)

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    game_type = "memory_match"
    title = factory.Sequence(lambda n: f"Game Config {n}")
    title_ar = factory.Sequence(lambda n: f"إعداد اللعبة {n}")
    title_fr = factory.Sequence(lambda n: f"Configuration {n}")
    subject = "arabic_letters"
    difficulty = "easy"
    target_age_min = 4
    target_age_max = 7
    config = factory.LazyAttribute(lambda o: _default_config(o.game_type))
    reward_stars = 10
    reward_xp = 15
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    is_active = True


__all__ = ["GameConfigFactory"]
