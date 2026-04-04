"""Seed reference MEN curricula for Collège 3ème demo flows."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import async_session
from app.models.men_compliance import MenCurriculum, MenObjective


def _trimester_for(index: int) -> int:
    if index <= 8:
        return 1
    if index <= 16:
        return 2
    return 3


def _build_objectives(
    subject_code: str,
    subject_titles: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (title_fr, title_ar) in enumerate(subject_titles, start=1):
        rows.append(
            {
                "code": f"{subject_code}-3C-{index:02d}",
                "title_fr": title_fr,
                "title_ar": title_ar,
                "description_fr": f"Objectif MEN de demonstration pour {title_fr.lower()}",
                "trimester": _trimester_for(index),
                "unit_number": ((index - 1) // 2) + 1,
                "is_mandatory": True,
                "hours_recommended": 2.0,
                "display_order": index,
            }
        )
    return rows


MATH_OBJECTIVES = _build_objectives(
    "MATH",
    [
        ("Reconnaitre les nombres rationnels", "التعرف على الأعداد الناطقة"),
        ("Comparer des fractions simples", "مقارنة الكسور البسيطة"),
        ("Additionner des fractions", "جمع الكسور"),
        ("Soustraire des fractions", "طرح الكسور"),
        ("Multiplier des nombres decimaux", "ضرب الأعداد العشرية"),
        ("Diviser des nombres decimaux", "قسمة الأعداد العشرية"),
        ("Resoudre une proportionnalite directe", "حل وضعية التناسب المباشر"),
        ("Utiliser le pourcentage dans un probleme", "استعمال النسبة المئوية في مسألة"),
        ("Representer un point dans le plan", "تمثيل نقطة في المستوى"),
        ("Calculer une distance sur repere", "حساب مسافة على معلم"),
        ("Construire un triangle avec contraintes", "إنشاء مثلث وفق معطيات"),
        ("Identifier les proprietes du parallelogramme", "تحديد خصائص متوازي الأضلاع"),
        ("Calculer le perimetre d une figure composee", "حساب محيط شكل مركب"),
        ("Calculer l aire d un triangle", "حساب مساحة مثلث"),
        ("Calculer le volume d un prisme droit", "حساب حجم منشور قائم"),
        ("Interpreter un tableau statistique", "قراءة جدول إحصائي"),
        ("Construire un diagramme en barres", "إنجاز مبيان بالأعمدة"),
        ("Calculer une moyenne simple", "حساب معدل بسيط"),
        ("Ecrire une expression algebrique", "كتابة عبارة جبرية"),
        ("Reduire une expression simple", "اختزال عبارة بسيطة"),
        ("Resoudre une equation du premier degre", "حل معادلة من الدرجة الأولى"),
        ("Verifier une egalite", "التحقق من مساواة"),
        ("Modeliser un probleme par equation", "نمذجة مسألة بمعادلة"),
        ("Lire une fonction lineaire", "قراءة دالة خطية"),
        ("Interpreter une representation graphique", "تفسير تمثيل بياني"),
    ],
)

ARABIC_OBJECTIVES = _build_objectives(
    "ARAB",
    [
        ("Lire un texte documentaire", "قراءة نص معلوماتي"),
        ("Degager l idee generale d un texte", "استخراج الفكرة العامة للنص"),
        ("Identifier les champs lexicaux", "تحديد الحقول المعجمية"),
        ("Distinguer narration et description", "التمييز بين السرد والوصف"),
        ("Reperer les articulateurs logiques", "رصد الروابط المنطقية"),
        ("Employer correctement la phrase nominale", "استعمال الجملة الاسمية بشكل صحيح"),
        ("Employer correctement la phrase verbale", "استعمال الجملة الفعلية بشكل صحيح"),
        ("Maitriser l accord sujet verbe", "إتقان المطابقة بين الفعل والفاعل"),
        ("Utiliser le complement d objet", "استعمال المفعول به"),
        ("Analyser un groupe nominal", "تحليل مركب اسمي"),
        ("Transformer un discours direct", "تحويل الخطاب المباشر"),
        ("Employer les signes de ponctuation", "استعمال علامات الترقيم"),
        ("Rediger un paragraphe coherent", "تحرير فقرة منسجمة"),
        ("Resumer un texte court", "تلخيص نص قصير"),
        ("Produire un texte narratif", "إنتاج نص سردي"),
        ("Produire un texte descriptif", "إنتاج نص وصفي"),
        ("Exprimer un point de vue argumente", "التعبير عن رأي معلل"),
        ("Identifier la these d un texte", "تحديد أطروحة النص"),
        ("Analyser une image support", "تحليل صورة داعمة"),
        ("Presenter oralement un sujet", "تقديم موضوع شفهيا"),
        ("Prendre des notes pendant l ecoute", "تدوين الملاحظات أثناء الاستماع"),
        ("Reutiliser un vocabulaire specifique", "إعادة توظيف معجم خاص"),
        ("Comparer deux textes", "مقارنة نصين"),
        ("Reviser un ecrit selon une grille", "مراجعة كتابة وفق شبكة"),
        ("Lire un poeme a haute voix", "قراءة قصيدة بصوت معبر"),
    ],
)

DEFAULT_CURRICULA: list[dict[str, Any]] = [
    {
        "level": "college",
        "grade": "3eme",
        "subject": "mathematics",
        "academic_year": "2025-2026",
        "version": "1.0",
        "objectives": MATH_OBJECTIVES,
    },
    {
        "level": "college",
        "grade": "3eme",
        "subject": "arabic",
        "academic_year": "2025-2026",
        "version": "1.0",
        "objectives": ARABIC_OBJECTIVES,
    },
]


async def seed_men_reference_data() -> tuple[int, int]:
    curricula_created = 0
    objectives_created = 0

    async with async_session() as session:
        try:
            for payload in DEFAULT_CURRICULA:
                curriculum = await session.scalar(
                    select(MenCurriculum).where(
                        MenCurriculum.level == payload["level"],
                        MenCurriculum.grade == payload["grade"],
                        MenCurriculum.subject == payload["subject"],
                        MenCurriculum.academic_year == payload["academic_year"],
                        MenCurriculum.version == payload["version"],
                    )
                )
                if curriculum is None:
                    curriculum = MenCurriculum(
                        level=payload["level"],
                        grade=payload["grade"],
                        subject=payload["subject"],
                        academic_year=payload["academic_year"],
                        version=payload["version"],
                    )
                    session.add(curriculum)
                    await session.flush()
                    curricula_created += 1

                existing_codes = {
                    row[0]
                    for row in (
                        await session.execute(
                            select(MenObjective.code).where(
                                MenObjective.curriculum_id == curriculum.id
                            )
                        )
                    ).all()
                }

                for objective_payload in payload["objectives"]:
                    if objective_payload["code"] in existing_codes:
                        continue
                    session.add(
                        MenObjective(
                            curriculum_id=curriculum.id,
                            **objective_payload,
                        )
                    )
                    objectives_created += 1

            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return curricula_created, objectives_created


async def main() -> None:
    curricula_created, objectives_created = await seed_men_reference_data()
    print(
        "men-curriculum-seed-ok "
        f"curricula_created={curricula_created} "
        f"objectives_created={objectives_created}"
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
