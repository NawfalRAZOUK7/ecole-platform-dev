"""Canonical taxonomy enums — single source of truth for closed vocabularies.

Aligned to the Moroccan national education system (MEN). **Four independent axes**
must never be conflated (see BACKEND_DB_AUDIT.md §10):

  * ``SchoolCycle``      — the STAGE: préscolaire → primaire → collège → lycée
  * ``ContentLevelBand`` — the NIVEAU (grade) inside a stage: PS…GS, 1AEP…6AEP, …
  * ``ContentSubject``   — the MATIÈRE (subject) taught
  * ``MicroSchoolType``  — the provider TYPE for informal (educator-run) schools

Closed sets are exposed as ``(str, enum.Enum)`` (matching ``RoleCode``) and applied
as native PostgreSQL enums via ``PgEnum(..., values_callable=enum_values)``.

Scope note (current): détaillé for **préscolaire + primaire**. Collège/lycée level
codes are present so existing data validates, but their per-niveau matière mapping
is intentionally left as TODO. Amazigh and Quranic subjects, and the msid Quranic
memorisation levels, are also TODO.
"""

from __future__ import annotations

import enum


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    """Return the string values for ``PgEnum(values_callable=...)``."""
    return [item.value for item in enum_cls]


def normalize_difficulty(value: str | None) -> str | None:
    """Accept any case from clients, return canonical UPPERCASE difficulty."""
    if value is None:
        return None
    cleaned = str(value).strip().upper()
    if cleaned not in DIFFICULTY_LEVELS:
        raise ValueError(
            f"difficulty must be one of {', '.join(DIFFICULTY_LEVELS)}"
        )
    return cleaned


def normalize_subject(value: str | None) -> str | None:
    """Validate against the canonical ``ContentSubject`` set (lowercase-coded)."""
    if value is None:
        return None
    cleaned = str(value).strip().lower()
    if cleaned not in CONTENT_SUBJECTS:
        raise ValueError(
            f"subject must be one of {', '.join(CONTENT_SUBJECTS)}"
        )
    return cleaned


def normalize_level_band(value: str | None) -> str | None:
    """Validate against the canonical ``ContentLevelBand`` set (case-sensitive)."""
    if value is None:
        return None
    cleaned = str(value).strip()
    if cleaned not in CONTENT_LEVEL_BANDS:
        raise ValueError(
            f"level_band must be one of {', '.join(CONTENT_LEVEL_BANDS)}"
        )
    return cleaned


class SchoolCycle(str, enum.Enum):
    """Education STAGE (niveau group), Moroccan system."""

    PRESCOLAIRE = "prescolaire"
    PRIMAIRE = "primaire"
    COLLEGE = "college"  # TODO: detailed niveaux/matières not yet modeled
    LYCEE = "lycee"  # TODO: detailed niveaux/matières not yet modeled


class MicroSchoolType(str, enum.Enum):
    """Provider TYPE for informal (educator-run) micro-schools.

    All are "informal schools" = ``MicroSchool``; they differ by who runs it /
    age group / purpose:
      * ``rawd``       — secular informal kindergarten (préscolaire)
      * ``msid``       — traditional Quranic school (faqih-run; Quran memorisation)
      * ``non_formel`` — 2e-chance / school-dropout reintegration
      * ``general``    — any other informal micro-school
    """

    RAWD = "rawd"
    MSID = "msid"
    NON_FORMEL = "non_formel"
    GENERAL = "general"


class ContentLevelBand(str, enum.Enum):
    """NIVEAU (grade) — Moroccan official codes.

    Détaillé pour préscolaire + primaire. Collège/lycée codes are kept so existing
    data validates; their per-niveau matière mapping is TODO.
    """

    # Préscolaire (and rawd)
    PS = "PS"
    MS = "MS"
    GS = "GS"
    # Primaire (6 ans)
    AEP1 = "1AEP"
    AEP2 = "2AEP"
    AEP3 = "3AEP"
    AEP4 = "4AEP"
    AEP5 = "5AEP"
    AEP6 = "6AEP"
    # Collège — TODO (codes kept so data fits; matière mapping not yet done)
    AC1 = "1AC"
    AC2 = "2AC"
    AC3 = "3AC"
    # Lycée — TODO
    TC = "TC"
    BAC1 = "1BAC"
    BAC2 = "2BAC"
    # TODO: msid Quranic memorisation stages (hifz levels)


class ContentSubject(str, enum.Enum):
    """MATIÈRE (subject) — Moroccan-official (combined science/social forms)."""

    # Languages
    ARABIC = "arabic"
    FRENCH = "french"
    ENGLISH = "english"
    AMAZIGH = "amazigh"  # official since 2011, progressive rollout

    # Math
    MATH = "math"

    # Sciences
    ACTIVITE_SCIENTIFIQUE = "activite_scientifique"  # primaire (éveil scientifique)
    SVT = "svt"  # collège/lycée — TODO detail
    PHYSIQUE_CHIMIE = "physique_chimie"  # collège/lycée — TODO detail

    # Humanities / social
    HISTOIRE_GEO = "histoire_geo"
    CIVIC = "civic"  # éducation à la citoyenneté
    PHILOSOPHY = "philosophy"  # lycée — TODO detail

    # Religious
    ISLAMIC = "islamic"  # éducation islamique
    QURANIC = "quranic"  # msid — Quran memorisation/recitation

    # Arts / EPS
    ART = "art"  # éducation artistique / arts plastiques
    MUSIC = "music"
    SPORT = "sport"  # éducation physique et sportive

    # Tech / économie
    INFORMATIQUE = "informatique"  # TICE
    TECHNOLOGY = "technology"
    ECONOMICS = "economics"  # lycée — TODO detail
    ACCOUNTING = "accounting"  # lycée — TODO detail

    # Early-literacy helpers (préscolaire / rawd / games like letter puzzles)
    ARABIC_LETTERS = "arabic_letters"
    LITERACY = "literacy"
    VOCABULARY = "vocabulary"

    # Teacher-facing resources
    PEDAGOGY = "pedagogy"

    # Escape hatch: a school-specific matière not in the official list. When a
    # column holds OTHER, the actual name is taken from a free-text companion
    # field (e.g. content_items.subject_other) — enum for the closed set + free
    # text for the open tail, like MicroSchool.type / type_detail.
    OTHER = "other"


class DifficultyLevel(str, enum.Enum):
    """Difficulty for content / quizzes / games. Canonical = UPPERCASE."""

    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class Language(str, enum.Enum):
    """UI / content language."""

    FR = "fr"
    AR = "ar"
    EN = "en"


class Currency(str, enum.Enum):
    """ISO-4217 currencies in use."""

    MAD = "MAD"
    EUR = "EUR"
    USD = "USD"


# --- Niveau → matières (which subjects a level may carry) ---------------------
# Détaillé for préscolaire + primaire only; collège/lycée = TODO. Used by
# validators / UI to offer only the subjects that exist at a given stage.

_PRESCOLAIRE_SUBJECTS: tuple[str, ...] = (
    "arabic", "french", "math", "activite_scientifique", "islamic",
    "art", "music", "sport",
    "arabic_letters", "literacy", "vocabulary",
)
_PRIMAIRE_SUBJECTS: tuple[str, ...] = (
    "arabic", "french", "english", "amazigh", "math", "activite_scientifique",
    "islamic", "histoire_geo", "civic", "art", "music", "sport",
    "informatique", "arabic_letters", "literacy", "vocabulary",
)
# Collège (enseignement secondaire collégial). Éveil scientifique du primaire se
# scinde en SVT + physique-chimie; pas de philosophie/économie (lycée).
_COLLEGE_SUBJECTS: tuple[str, ...] = (
    "arabic", "french", "english", "amazigh", "math", "svt", "physique_chimie",
    "histoire_geo", "civic", "islamic", "art", "sport", "informatique",
    "technology",
)
# Lycée (enseignement secondaire qualifiant). Ajoute philosophie, économie et
# comptabilité; histoire-géo + éducation islamique restent au tronc commun.
_LYCEE_SUBJECTS: tuple[str, ...] = (
    "arabic", "french", "english", "math", "svt", "physique_chimie",
    "histoire_geo", "civic", "philosophy", "islamic", "sport", "informatique",
    "economics", "accounting", "technology",
)

#: Stage → allowed matières (official MEN, by cycle).
CYCLE_SUBJECTS: dict[str, tuple[str, ...]] = {
    SchoolCycle.PRESCOLAIRE.value: _PRESCOLAIRE_SUBJECTS,
    SchoolCycle.PRIMAIRE.value: _PRIMAIRE_SUBJECTS,
    SchoolCycle.COLLEGE.value: _COLLEGE_SUBJECTS,
    SchoolCycle.LYCEE.value: _LYCEE_SUBJECTS,
}


def subjects_for_cycle(cycle: str) -> tuple[str, ...]:
    """Return the matières valid for a stage (empty tuple if not yet modeled)."""
    return CYCLE_SUBJECTS.get(cycle, ())


#: String value tuples, reused by Pydantic validators and CHECK/enum migrations.
SCHOOL_CYCLES: tuple[str, ...] = tuple(e.value for e in SchoolCycle)
MICRO_SCHOOL_TYPES: tuple[str, ...] = tuple(e.value for e in MicroSchoolType)
CONTENT_LEVEL_BANDS: tuple[str, ...] = tuple(e.value for e in ContentLevelBand)
CONTENT_SUBJECTS: tuple[str, ...] = tuple(e.value for e in ContentSubject)
DIFFICULTY_LEVELS: tuple[str, ...] = tuple(e.value for e in DifficultyLevel)
LANGUAGES: tuple[str, ...] = tuple(e.value for e in Language)
CURRENCIES: tuple[str, ...] = tuple(e.value for e in Currency)
