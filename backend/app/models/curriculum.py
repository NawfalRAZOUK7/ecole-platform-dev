"""Official Moroccan curriculum structure — Cycle → Niveau → Matière → Topics.

**Backend source of truth** for the curriculum tree (NOT seed data). Read by
validators, services and the public `/curriculum` API so the platform — and the
frontend — always derive the official structure from one place.

Scope (decided): **PRIVATE / "formal" sector**, **préscolaire + primaire** only.
Out of scope for now (documented TODO): public sector, collège/lycée, amazigh &
quranic matières, msid (Quranic) levels.

Terminology (kept strictly distinct in code):
  * **cycle**   — stage: ``prescolaire``, ``primaire`` (``SchoolCycle``).
  * **niveau / level** — grade inside a cycle: ``PS/MS/GS``, ``1AEP…6AEP``
    (``ContentLevelBand``).
  * **matière** — *= subject*. Code uses ``subject`` everywhere; "matière" is the
    French label for the same thing (``ContentSubject``).
  * **sujet**   — a topic/chapter inside a matière at a level. Code uses
    **``topic``** (never "subject") to avoid confusion with matière.

Sources (official MEN + sector practice):
  - Primaire = 6 yrs, 2 sub-cycles (1er: 1–2AEP ; 2e: 3–6AEP). French taught
    from 1AEP in public since 2017/2018; private/trilingue schools teach French
    from préscolaire and English from ~3AEP (Cambridge). Social studies
    (الاجتماعيات / histoire-géo) begins in the 2e cycle (3AEP).
  See EDUCATION_TAXONOMY.md for the full source list.
"""

from __future__ import annotations

import enum

from app.models.taxonomy import ContentLevelBand, SchoolCycle


class SchoolSector(str, enum.Enum):
    """Education sector. Only PRIVATE (the platform's *formal* target) is
    modeled now; PUBLIC differs (e.g. French from 1AEP, English at collège)
    and is a documented TODO."""

    PRIVATE = "private"  # "formal" — trilingue (French from préscolaire, English ~3AEP)
    PUBLIC = "public"  # TODO


# --- Cycle → ordered niveaux (scope: préscolaire + primaire) ----------------
LEVELS_BY_CYCLE: dict[str, tuple[str, ...]] = {
    SchoolCycle.PRESCOLAIRE.value: (
        ContentLevelBand.PS.value,
        ContentLevelBand.MS.value,
        ContentLevelBand.GS.value,
    ),
    SchoolCycle.PRIMAIRE.value: (
        ContentLevelBand.AEP1.value,
        ContentLevelBand.AEP2.value,
        ContentLevelBand.AEP3.value,
        ContentLevelBand.AEP4.value,
        ContentLevelBand.AEP5.value,
        ContentLevelBand.AEP6.value,
    ),
    SchoolCycle.COLLEGE.value: (
        ContentLevelBand.AC1.value,
        ContentLevelBand.AC2.value,
        ContentLevelBand.AC3.value,
    ),
    SchoolCycle.LYCEE.value: (
        ContentLevelBand.TC.value,
        ContentLevelBand.BAC1.value,
        ContentLevelBand.BAC2.value,
    ),
}
LEVEL_TO_CYCLE: dict[str, str] = {
    level: cycle for cycle, levels in LEVELS_BY_CYCLE.items() for level in levels
}

# --- Matières per niveau (PRIVATE sector) -----------------------------------
# Préscolaire (PS/MS/GS): trilingue private => French present; English not yet.
_PRESCOLAIRE_MATIERES: tuple[str, ...] = (
    "arabic",
    "french",
    "math",
    "activite_scientifique",
    "islamic",
    "art",
    "music",
    "sport",
    "arabic_letters",
    "literacy",
    "vocabulary",
)
# Primaire 1er cycle (1AEP–2AEP): languages + math + science + islamic + arts/sport.
_PRIMAIRE_1ER_CYCLE: tuple[str, ...] = (
    "arabic",
    "french",
    "math",
    "activite_scientifique",
    "islamic",
    "art",
    "music",
    "sport",
    "arabic_letters",
    "literacy",
    "vocabulary",
)
# Primaire 2e cycle (3AEP–6AEP): adds English (private), social studies, civic, TICE.
_PRIMAIRE_2E_CYCLE: tuple[str, ...] = (
    "arabic",
    "french",
    "english",
    "math",
    "activite_scientifique",
    "islamic",
    "histoire_geo",
    "civic",
    "informatique",
    "art",
    "music",
    "sport",
)
# Collège (1AC–3AC): éveil scientifique du primaire se scinde en SVT +
# physique-chimie; pas encore de philosophie/économie (lycée).
_COLLEGE_MATIERES: tuple[str, ...] = (
    "arabic",
    "french",
    "english",
    "amazigh",
    "math",
    "svt",
    "physique_chimie",
    "histoire_geo",
    "civic",
    "islamic",
    "art",
    "sport",
    "informatique",
    "technology",
)
# Lycée (TC–2BAC): ajoute philosophie, économie et comptabilité.
_LYCEE_MATIERES: tuple[str, ...] = (
    "arabic",
    "french",
    "english",
    "math",
    "svt",
    "physique_chimie",
    "histoire_geo",
    "civic",
    "philosophy",
    "islamic",
    "sport",
    "informatique",
    "economics",
    "accounting",
    "technology",
)

MATIERES_BY_LEVEL: dict[str, tuple[str, ...]] = {
    ContentLevelBand.PS.value: _PRESCOLAIRE_MATIERES,
    ContentLevelBand.MS.value: _PRESCOLAIRE_MATIERES,
    ContentLevelBand.GS.value: _PRESCOLAIRE_MATIERES,
    ContentLevelBand.AEP1.value: _PRIMAIRE_1ER_CYCLE,
    ContentLevelBand.AEP2.value: _PRIMAIRE_1ER_CYCLE,
    ContentLevelBand.AEP3.value: _PRIMAIRE_2E_CYCLE,
    ContentLevelBand.AEP4.value: _PRIMAIRE_2E_CYCLE,
    ContentLevelBand.AEP5.value: _PRIMAIRE_2E_CYCLE,
    ContentLevelBand.AEP6.value: _PRIMAIRE_2E_CYCLE,
    ContentLevelBand.AC1.value: _COLLEGE_MATIERES,
    ContentLevelBand.AC2.value: _COLLEGE_MATIERES,
    ContentLevelBand.AC3.value: _COLLEGE_MATIERES,
    ContentLevelBand.TC.value: _LYCEE_MATIERES,
    ContentLevelBand.BAC1.value: _LYCEE_MATIERES,
    ContentLevelBand.BAC2.value: _LYCEE_MATIERES,
}

# --- Topics (sujets) per (niveau, matière) — REPRESENTATIVE starter set ------
# Not exhaustive; the structure is official, the topic lists are a sensible
# starter (French labels) that can be enriched toward the full MEN programme.
# Empty / missing (level, matière) => no topics seeded yet (still a valid matière).
TOPICS_BY_LEVEL_MATIERE: dict[tuple[str, str], tuple[str, ...]] = {
    # Préscolaire (shared representative themes across PS/MS/GS) ---------------
    ("GS", "arabic"): ("الحروف الهجائية", "الأصوات والمقاطع", "القراءة الأولية"),
    ("GS", "french"): ("Les sons et les lettres", "Le vocabulaire du quotidien", "La comptine"),
    ("GS", "math"): ("Les nombres de 1 à 10", "Les formes", "Grand/petit, plus/moins"),
    ("GS", "activite_scientifique"): ("Le corps humain", "Les animaux", "Les saisons"),
    # Primaire — Mathématiques (per level) ------------------------------------
    ("1AEP", "math"): ("Les nombres de 0 à 20", "Comparer et ranger", "Les formes géométriques", "L'addition", "La soustraction"),
    ("2AEP", "math"): ("Les nombres jusqu'à 100", "Addition et soustraction avec retenue", "Introduction à la multiplication", "La monnaie et le temps", "Les figures géométriques"),
    ("3AEP", "math"): ("Les nombres jusqu'à 1000", "Les tables de multiplication", "La division", "Les fractions simples", "Le périmètre", "La symétrie"),
    ("4AEP", "math"): ("Les grands nombres", "Multiplication et division posées", "Les fractions", "Les nombres décimaux", "Périmètre et aire", "Les angles"),
    ("5AEP", "math"): ("Opérations sur les décimaux", "Les fractions équivalentes", "La proportionnalité", "Aire et volume", "Les unités de mesure"),
    ("6AEP", "math"): ("Les nombres décimaux", "Les pourcentages", "La proportionnalité", "Aire, périmètre et volume", "Résolution de problèmes"),
    # Primaire — Arabe (représentatif) ----------------------------------------
    ("1AEP", "arabic"): ("الحروف والأصوات", "القراءة", "الخط والكتابة"),
    ("3AEP", "arabic"): ("القراءة والفهم", "قواعد اللغة (الاسم والفعل)", "التعبير الكتابي", "الإملاء"),
    ("6AEP", "arabic"): ("النصوص القرائية", "الصرف والتحويل", "الإنشاء", "النحو"),
    # Primaire — Français (représentatif) -------------------------------------
    ("1AEP", "french"): ("Les sons et les lettres", "Lecture de syllabes", "Écriture"),
    ("3AEP", "french"): ("Lecture et compréhension", "Grammaire : le verbe", "Conjugaison : le présent", "Production écrite"),
    ("6AEP", "french"): ("Compréhension de texte", "Grammaire et conjugaison", "La rédaction", "Vocabulaire et orthographe"),
    # Primaire — Activité scientifique (représentatif) ------------------------
    ("3AEP", "activite_scientifique"): ("La matière et ses états", "Les plantes", "Le corps humain"),
    ("6AEP", "activite_scientifique"): ("La digestion et la respiration", "L'électricité", "L'environnement et le recyclage"),
    # Primaire — Histoire-Géo (2e cycle) --------------------------------------
    ("3AEP", "histoire_geo"): ("Mon environnement proche", "Le temps et le calendrier", "La carte et l'espace"),
    ("6AEP", "histoire_geo"): ("Le Maroc : géographie", "Repères historiques du Maroc", "Lecture de cartes"),
}


# --- Official matière titles (AR / FR / EN) — official MEN naming ------------
# Source of truth for the *official* label of each subject code. Custom matières
# carry their own user-supplied title (stored in the DB, see CustomSubject).
SUBJECT_TITLES: dict[str, dict[str, str]] = {
    "arabic": {"ar": "اللغة العربية", "fr": "Langue arabe", "en": "Arabic"},
    "french": {"ar": "اللغة الفرنسية", "fr": "Langue française", "en": "French"},
    "english": {"ar": "اللغة الإنجليزية", "fr": "Langue anglaise", "en": "English"},
    "amazigh": {"ar": "اللغة الأمازيغية", "fr": "Langue amazighe", "en": "Amazigh"},
    "arabic_letters": {"ar": "الحروف العربية", "fr": "Lettres arabes", "en": "Arabic letters"},
    "math": {"ar": "الرياضيات", "fr": "Mathématiques", "en": "Mathematics"},
    "activite_scientifique": {"ar": "النشاط العلمي", "fr": "Activité scientifique", "en": "Scientific activity"},
    "svt": {"ar": "علوم الحياة والأرض", "fr": "Sciences de la vie et de la Terre", "en": "Life & earth sciences"},
    "physique_chimie": {"ar": "الفيزياء والكيمياء", "fr": "Physique-Chimie", "en": "Physics-Chemistry"},
    "histoire_geo": {"ar": "الاجتماعيات", "fr": "Éducation sociale (histoire-géographie)", "en": "Social studies"},
    "civic": {"ar": "التربية على المواطنة", "fr": "Éducation à la citoyenneté", "en": "Civic education"},
    "philosophy": {"ar": "الفلسفة", "fr": "Philosophie", "en": "Philosophy"},
    "islamic": {"ar": "التربية الإسلامية", "fr": "Éducation islamique", "en": "Islamic education"},
    "quranic": {"ar": "القرآن الكريم (حفظ وتجويد)", "fr": "Coran (mémorisation)", "en": "Quran (memorisation)"},
    "art": {"ar": "التربية الفنية", "fr": "Éducation artistique", "en": "Arts"},
    "music": {"ar": "التربية الموسيقية", "fr": "Éducation musicale", "en": "Music"},
    "sport": {"ar": "التربية البدنية", "fr": "Éducation physique", "en": "Physical education"},
    "informatique": {"ar": "المعلوميات", "fr": "Informatique (TICE)", "en": "Computing"},
    "technology": {"ar": "التكنولوجيا", "fr": "Technologie", "en": "Technology"},
    "economics": {"ar": "الاقتصاد", "fr": "Économie", "en": "Economics"},
    "accounting": {"ar": "المحاسبة", "fr": "Comptabilité", "en": "Accounting"},
    "literacy": {"ar": "القراءة الأولية", "fr": "Pré-lecture", "en": "Literacy"},
    "vocabulary": {"ar": "المفردات", "fr": "Vocabulaire", "en": "Vocabulary"},
    "pedagogy": {"ar": "البيداغوجيا", "fr": "Pédagogie", "en": "Pedagogy"},
}


def subject_title(subject: str, locale: str = "fr", default_locale: str = "fr") -> str:
    """Official title of a matière in a locale; falls back to fr then the code."""
    titles = SUBJECT_TITLES.get(subject, {})
    return titles.get(locale) or titles.get(default_locale) or subject


def is_official_subject(subject: str) -> bool:
    """True if `subject` is an official MEN matière (vs a school custom one)."""
    return subject in SUBJECT_TITLES


# --- Public helpers (the API + validators read THESE, never seed) -----------
def cycle_for_level(level: str) -> str | None:
    """Return the cycle a niveau belongs to, or None if out of scope."""
    return LEVEL_TO_CYCLE.get(level)


def levels_for_cycle(cycle: str) -> tuple[str, ...]:
    return LEVELS_BY_CYCLE.get(cycle, ())


def matieres_for_level(level: str) -> tuple[str, ...]:
    """Official matières (subjects) offered at a niveau (PRIVATE sector)."""
    return MATIERES_BY_LEVEL.get(level, ())


def topics_for(level: str, subject: str) -> tuple[str, ...]:
    """Representative topics (sujets) for a (niveau, matière)."""
    return TOPICS_BY_LEVEL_MATIERE.get((level, subject), ())


def is_subject_valid_for_level(subject: str, level: str) -> bool:
    """True iff `subject` (matière) is taught at `level` (niveau) in scope.

    Returns True when the level is out of the modeled scope (PS/MS/GS, AEP) so
    collège/lycée content is not blocked while their detail is still TODO.
    """
    matieres = MATIERES_BY_LEVEL.get(level)
    if matieres is None:
        return True  # level outside the modeled scope → don't over-constrain
    return subject in matieres


def curriculum_tree() -> list[dict]:
    """Full nested structure for the public `/curriculum` API:
    [{cycle, levels: [{level, matieres: [{subject, topics: [...]}]}]}]."""
    tree: list[dict] = []
    for cycle, levels in LEVELS_BY_CYCLE.items():
        tree.append(
            {
                "cycle": cycle,
                "levels": [
                    {
                        "level": level,
                        "matieres": [
                            {
                                "subject": subject,
                                "title": SUBJECT_TITLES.get(subject, {}),
                                "official": True,
                                "topics": list(topics_for(level, subject)),
                            }
                            for subject in matieres_for_level(level)
                        ],
                    }
                    for level in levels
                ],
            }
        )
    return tree
