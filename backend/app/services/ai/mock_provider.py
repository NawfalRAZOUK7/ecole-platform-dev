"""Realistic no-network AI provider used by default."""

from __future__ import annotations

from typing import Any

from app.services.ai.provider_base import Recommendation, WritingFeedback


class MockProvider:
    """Keyword- and heuristic-based provider with useful fallback responses."""

    def _resolve_language(self, language: str | None, text: str) -> str:
        normalized = str(language or "").lower()
        if normalized in {"fr", "ar", "en"}:
            return normalized
        if any("\u0600" <= char <= "\u06ff" for char in text):
            return "ar"
        lowered = text.lower()
        if any(word in lowered for word in ("le ", "la ", "les ", "pour ", "avec ")):
            return "fr"
        return "en"

    def _complete_text(self, prompt: str, language: str) -> str:
        lowered = prompt.lower()
        if any(keyword in lowered for keyword in ("grade", "note", "score", "result")):
            messages = {
                "fr": "Les résultats montrent une progression régulière. Priorisez les notions où la moyenne reste sous le seuil attendu.",
                "ar": "تُظهر النتائج تقدماً منتظماً. ركزوا أولاً على المهارات التي ما زال مستواها دون العتبة المطلوبة.",
                "en": "The results show steady progress. Prioritize the skills that are still below the expected benchmark first.",
            }
            return messages[language]
        if any(keyword in lowered for keyword in ("attendance", "presence", "absen")):
            messages = {
                "fr": "La présence reste globalement correcte, mais une hausse récente des absences mérite un suivi rapide avec les familles concernées.",
                "ar": "الحضور مقبول بشكل عام، لكن الارتفاع الأخير في الغيابات يستدعي متابعة سريعة مع الأسر المعنية.",
                "en": "Attendance is broadly stable, but the recent increase in absences warrants quick follow-up with the affected families.",
            }
            return messages[language]
        messages = {
            "fr": "Voici une synthèse claire et exploitable basée sur les données fournies, avec des priorités concrètes pour la prochaine étape.",
            "ar": "إليك خلاصة واضحة وقابلة للتنفيذ استناداً إلى المعطيات المتاحة، مع أولويات عملية للمرحلة التالية.",
            "en": "Here is a clear, actionable summary based on the available information, with practical next-step priorities.",
        }
        return messages[language]

    async def complete(self, prompt: str, system: str, max_tokens: int = 1024) -> str:
        language = self._resolve_language(None, f"{system}\n{prompt}")
        return self._complete_text(prompt, language)[:max_tokens]

    async def analyze_writing(self, text: str, language: str) -> WritingFeedback:
        resolved_language = self._resolve_language(language, text)
        words = [word for word in text.split() if word.strip()]
        word_count = len(words)
        sentence_count = max(1, sum(text.count(mark) for mark in ".!?؟"))

        if word_count < 20:
            suggestions = {
                "fr": "Développe davantage ton idée principale avec un exemple concret et une phrase de conclusion.",
                "ar": "وسّع الفكرة الرئيسية بإضافة مثال واضح وجملة ختامية قصيرة.",
                "en": "Develop your main idea further by adding a concrete example and a short concluding sentence.",
            }
            hints_map = {
                "fr": [
                    "Ajoute un exemple précis qui illustre ton point principal.",
                    "Relis l'introduction pour vérifier qu'elle annonce bien le sujet.",
                ],
                "ar": [
                    "أضف مثالاً محدداً يوضح الفكرة الأساسية.",
                    "راجع المقدمة للتأكد من أنها تمهد للموضوع بوضوح.",
                ],
                "en": [
                    "Add one specific example that supports your main point.",
                    "Re-read the introduction to make sure it clearly sets up the topic.",
                ],
            }
        elif word_count < 100:
            suggestions = {
                "fr": "Le texte est bien lancé. Renforce maintenant l'organisation des paragraphes et la conclusion.",
                "ar": "النص بدأ بشكل جيد. ركز الآن على تنظيم الفقرات وتقوية الخاتمة.",
                "en": "The draft is off to a good start. Focus next on paragraph structure and a stronger conclusion.",
            }
            hints_map = {
                "fr": [
                    "Vérifie que chaque paragraphe développe une seule idée principale.",
                    "Ajoute une phrase finale qui résume ta position ou ton message.",
                    "Varie les connecteurs pour mieux relier les idées.",
                ],
                "ar": [
                    "تأكد من أن كل فقرة تطور فكرة رئيسية واحدة.",
                    "أضف جملة أخيرة تلخص الرسالة أو الموقف.",
                    "نوع أدوات الربط حتى تنتقل الأفكار بسلاسة.",
                ],
                "en": [
                    "Check that each paragraph develops one main idea.",
                    "Add a final sentence that sums up your message or position.",
                    "Vary linking words so the ideas flow more smoothly.",
                ],
            }
        else:
            suggestions = {
                "fr": "Le contenu est solide. La prochaine amélioration doit viser la précision du vocabulaire et la fluidité des transitions.",
                "ar": "المحتوى متماسك. الخطوة التالية هي تحسين دقة المفردات وسلاسة الانتقال بين الأفكار.",
                "en": "The content is solid. The next improvement should focus on vocabulary precision and smoother transitions.",
            }
            hints_map = {
                "fr": [
                    "Repère les répétitions et remplace-les par un vocabulaire plus précis.",
                    "Relis les phrases longues pour vérifier qu'elles restent claires.",
                    "Contrôle la ponctuation pour mieux rythmer le texte.",
                ],
                "ar": [
                    "حدد الكلمات المكررة واستبدلها بمفردات أدق.",
                    "راجع الجمل الطويلة للتأكد من وضوحها.",
                    "اضبط علامات الترقيم لتحسين إيقاع النص.",
                ],
                "en": [
                    "Spot repeated words and replace them with more precise vocabulary.",
                    "Review long sentences to make sure they stay clear.",
                    "Check punctuation to improve rhythm and readability.",
                ],
            }

        if sentence_count <= 1:
            hints_map[resolved_language].append(
                {
                    "fr": "Essaie de découper le texte en plusieurs phrases pour clarifier le raisonnement.",
                    "ar": "حاول تقسيم النص إلى عدة جمل لتوضيح التسلسل المنطقي.",
                    "en": "Try splitting the text into multiple sentences to make the reasoning clearer.",
                }[resolved_language]
            )

        return {
            "suggestion": suggestions[resolved_language],
            "hints": hints_map[resolved_language][:3],
            "word_count": word_count,
        }

    async def generate_recommendations(
        self,
        student_data: dict[str, Any],
        language: str | None = None,
    ) -> list[Recommendation]:
        completed_count = int(student_data.get("completed_count") or 0)
        average_grade = float(student_data.get("average_grade") or 0)
        level_band = str(student_data.get("level_band") or "").upper()
        recent_topics = [str(item) for item in student_data.get("recent_topics") or []]

        recommendations: list[Recommendation] = []
        if completed_count < 5:
            recommendations.append(
                {
                    "title": "Complete one foundational learning module this week",
                    "reason_code": "LOW_COMPLETION",
                    "priority": "high",
                    "content_type": "module",
                }
            )
        if average_grade and average_grade < 10:
            recommendations.append(
                {
                    "title": "Review the last assessed concepts before attempting new work",
                    "reason_code": "GRADE_BELOW_EXPECTATION",
                    "priority": "high",
                    "content_type": "revision",
                }
            )
        elif average_grade >= 16:
            recommendations.append(
                {
                    "title": "Unlock an extension activity to deepen mastery",
                    "reason_code": "HIGH_PERFORMANCE",
                    "priority": "medium",
                    "content_type": "enrichment",
                }
            )
        if level_band in {"CP", "CE1", "CE2"}:
            recommendations.append(
                {
                    "title": "Add a short reading-comprehension practice session",
                    "reason_code": "LEVEL_APPROPRIATE",
                    "priority": "medium",
                    "content_type": "activity",
                }
            )
        if recent_topics:
            recommendations.append(
                {
                    "title": f"Continue practicing {recent_topics[0]} with one targeted exercise",
                    "reason_code": "TOPIC_CONTINUATION",
                    "priority": "medium",
                    "content_type": "exercise",
                }
            )
        if not recommendations:
            recommendations.append(
                {
                    "title": "Explore the content library for a new topic aligned with current coursework",
                    "reason_code": "GENERAL_EXPLORATION",
                    "priority": "low",
                    "content_type": "library",
                }
            )
        return recommendations[:3]

    async def compute_kpi_insights(self, metrics: dict[str, Any]) -> list[str]:
        insights: list[str] = []
        for metric in metrics.get("kpis") or []:
            name = str(metric.get("name") or metric.get("kpi_id") or "metric")
            value = metric.get("value")
            threshold = str(metric.get("threshold") or "").lower()
            if value is None:
                continue
            if "critical" in threshold or (
                isinstance(value, (int, float)) and value < 0
            ):
                insights.append(
                    f"{name} needs immediate review because it is outside the expected range."
                )
            elif isinstance(value, (int, float)) and value == 0:
                insights.append(
                    f"{name} is flat for the selected period; verify whether this reflects real inactivity or missing data."
                )
            elif isinstance(value, (int, float)) and value > 0:
                insights.append(
                    f"{name} shows measurable activity; compare it with the previous period to confirm the trend."
                )
        if not insights:
            insights.append(
                "Current KPI signals are broadly stable, with no immediate anomalies detected in the selected period."
            )
        return insights[:4]
