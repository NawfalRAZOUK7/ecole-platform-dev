"""Service layer for MEN compliance workflows."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.permissions import SUP, SYS
from app.core.unit_of_work import UnitOfWork
from app.domain.events.men_compliance import (
    ComplianceReportGenerated,
    CurriculumMapped,
    MenCurriculumCreated,
    MenCurriculumSeeded,
    MenObjectiveCreated,
)
from app.models.men_compliance import (
    ComplianceReport,
    CurriculumMapping,
    MenCurriculum,
    MenObjective,
)
from app.repositories.admin_men_compliance import ComplianceRepository
from app.schemas.admin.men_compliance import (
    ComplianceDashboardItemResponse,
    ComplianceDashboardResponse,
    ComplianceReportGenerateRequest,
    ComplianceReportResponse,
    CurriculumMappingCreateRequest,
    CurriculumMappingResponse,
    MenCurriculumCreateRequest,
    MenCurriculumResponse,
    MenObjectiveCreateRequest,
    MenObjectiveResponse,
)
from app.services.platform.audit import AuditService
from app.services.communication.event_dispatcher import EventDispatcher


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value is not None else None


def _trimester_for(index: int) -> int:
    if index <= 8:
        return 1
    if index <= 16:
        return 2
    return 3


def _build_seed_objectives(
    subject_code: str,
    subject_titles: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    objectives: list[dict[str, Any]] = []
    for index, (title_fr, title_ar) in enumerate(subject_titles, start=1):
        objectives.append(
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
    return objectives


DEFAULT_CURRICULA: list[dict[str, Any]] = [
    {
        "level": "college",
        "grade": "3eme",
        "subject": "mathematics",
        "academic_year": "2025-2026",
        "version": "1.0",
        "objectives": _build_seed_objectives(
            "MATH",
            [
                ("Reconnaitre les nombres rationnels", "التعرف على الأعداد الناطقة"),
                ("Comparer des fractions simples", "مقارنة الكسور البسيطة"),
                ("Additionner des fractions", "جمع الكسور"),
                ("Soustraire des fractions", "طرح الكسور"),
                ("Multiplier des nombres decimaux", "ضرب الأعداد العشرية"),
                ("Diviser des nombres decimaux", "قسمة الأعداد العشرية"),
                ("Resoudre une proportionnalite directe", "حل وضعية التناسب المباشر"),
                (
                    "Utiliser le pourcentage dans un probleme",
                    "استعمال النسبة المئوية في مسألة",
                ),
                ("Representer un point dans le plan", "تمثيل نقطة في المستوى"),
                ("Calculer une distance sur repere", "حساب مسافة على معلم"),
                ("Construire un triangle avec contraintes", "إنشاء مثلث وفق معطيات"),
                (
                    "Identifier les proprietes du parallelogramme",
                    "تحديد خصائص متوازي الأضلاع",
                ),
                ("Calculer le perimetre d une figure composee", "حساب محيط شكل مركب"),
                ("Calculer l aire d un triangle", "حساب مساحة مثلث"),
                ("Calculer le volume d un prisme droit", "حساب حجم منشور قائم"),
                ("Interpreter un tableau statistique", "قراءة جدول إحصائي"),
                ("Construire un diagramme en barres", "إنجاز مبيان بالأعمدة"),
                ("Calculer une moyenne simple", "حساب معدل بسيط"),
                ("Ecrire une expression algebrique", "كتابة عبارة جبرية"),
                ("Reduire une expression simple", "اختزال عبارة بسيطة"),
                (
                    "Resoudre une equation du premier degre",
                    "حل معادلة من الدرجة الأولى",
                ),
                ("Verifier une egalite", "التحقق من مساواة"),
                ("Modeliser un probleme par equation", "نمذجة مسألة بمعادلة"),
                ("Lire une fonction lineaire", "قراءة دالة خطية"),
                ("Interpreter une representation graphique", "تفسير تمثيل بياني"),
            ],
        ),
    },
    {
        "level": "college",
        "grade": "3eme",
        "subject": "arabic",
        "academic_year": "2025-2026",
        "version": "1.0",
        "objectives": _build_seed_objectives(
            "ARAB",
            [
                ("Lire un texte documentaire", "قراءة نص معلوماتي"),
                ("Degager l idee generale d un texte", "استخراج الفكرة العامة للنص"),
                ("Identifier les champs lexicaux", "تحديد الحقول المعجمية"),
                ("Distinguer narration et description", "التمييز بين السرد والوصف"),
                ("Reperer les articulateurs logiques", "رصد الروابط المنطقية"),
                (
                    "Employer correctement la phrase nominale",
                    "استعمال الجملة الاسمية بشكل صحيح",
                ),
                (
                    "Employer correctement la phrase verbale",
                    "استعمال الجملة الفعلية بشكل صحيح",
                ),
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
                (
                    "Prendre des notes pendant l ecoute",
                    "تدوين الملاحظات أثناء الاستماع",
                ),
                ("Reutiliser un vocabulaire specifique", "إعادة توظيف معجم خاص"),
                ("Comparer deux textes", "مقارنة نصين"),
                ("Reviser un ecrit selon une grille", "مراجعة كتابة وفق شبكة"),
                ("Lire un poeme a haute voix", "قراءة قصيدة بصوت معبر"),
            ],
        ),
    },
]


class ComplianceService:
    """Business logic for MEN curricula, mappings, reports, and seed data."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ComplianceRepository(db)
        self.audit = AuditService(db)
        self._dispatcher = EventDispatcher(db)

    def _ensure_seed_role(self, auth: AuthContext) -> None:
        if auth.role not in {SUP, SYS}:
            raise ValidationError(
                "Only SUP and SYS can manage MEN reference data",
                error_code="ERR-COMPLY-422",
            )

    def _curriculum_to_response(self, curriculum: MenCurriculum) -> dict[str, Any]:
        return MenCurriculumResponse(
            id=str(curriculum.id),
            level=curriculum.level,
            grade=curriculum.grade,
            subject=curriculum.subject,
            academic_year=curriculum.academic_year,
            version=curriculum.version,
            is_active=curriculum.is_active,
            created_at=_iso(curriculum.created_at) or "",
            updated_at=_iso(curriculum.updated_at),
        ).model_dump()

    def _objective_to_response(self, objective: MenObjective) -> dict[str, Any]:
        return MenObjectiveResponse(
            id=str(objective.id),
            curriculum_id=str(objective.curriculum_id),
            curriculum_subject=(
                objective.curriculum.subject
                if objective.curriculum is not None
                else None
            ),
            code=objective.code,
            title_fr=objective.title_fr,
            title_ar=objective.title_ar,
            description_fr=objective.description_fr,
            trimester=objective.trimester,
            unit_number=objective.unit_number,
            is_mandatory=objective.is_mandatory,
            hours_recommended=(
                float(objective.hours_recommended)
                if objective.hours_recommended is not None
                else None
            ),
            display_order=objective.display_order,
            created_at=_iso(objective.created_at) or "",
            updated_at=_iso(objective.updated_at),
        ).model_dump()

    def _mapping_to_response(self, mapping: CurriculumMapping) -> dict[str, Any]:
        objective = mapping.objective
        curriculum = objective.curriculum if objective is not None else None
        return CurriculumMappingResponse(
            id=str(mapping.id),
            school_id=str(mapping.school_id),
            objective_id=str(mapping.objective_id),
            objective_code=objective.code if objective is not None else None,
            curriculum_id=str(curriculum.id) if curriculum is not None else None,
            course_id=str(mapping.course_id) if mapping.course_id is not None else None,
            content_item_id=(
                str(mapping.content_item_id)
                if mapping.content_item_id is not None
                else None
            ),
            mapped_by=str(mapping.mapped_by),
            mapped_at=_iso(mapping.mapped_at) or "",
            coverage_percent=mapping.coverage_percent,
            notes=mapping.notes,
            created_at=_iso(mapping.created_at) or "",
            updated_at=_iso(mapping.updated_at),
        ).model_dump()

    def _report_to_response(self, report: ComplianceReport) -> dict[str, Any]:
        curriculum = report.curriculum
        return ComplianceReportResponse(
            id=str(report.id),
            school_id=str(report.school_id),
            curriculum_id=str(report.curriculum_id),
            curriculum_subject=curriculum.subject if curriculum is not None else None,
            curriculum_grade=curriculum.grade if curriculum is not None else None,
            curriculum_level=curriculum.level if curriculum is not None else None,
            generated_at=_iso(report.generated_at) or "",
            generated_by=str(report.generated_by),
            total_objectives=report.total_objectives,
            mapped_objectives=report.mapped_objectives,
            compliance_percent=float(report.compliance_percent),
            unmapped_objectives=list(report.unmapped_objectives or []),
            pdf_url=report.pdf_url,
            academic_year_id=str(report.academic_year_id),
            created_at=_iso(report.created_at) or "",
            updated_at=_iso(report.updated_at),
        ).model_dump()

    def _report_url(self, report_id: uuid.UUID) -> str:
        return f"/generated/compliance-reports/{report_id}.pdf"

    def _build_minimal_pdf(self, lines: list[str]) -> bytes:
        def escape(value: str) -> str:
            return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

        content_lines = ["BT", "/F1 12 Tf", "50 760 Td"]
        for index, line in enumerate(lines):
            if index:
                content_lines.append("0 -16 Td")
            content_lines.append(f"({escape(line)}) Tj")
        content_lines.append("ET")
        stream = "\n".join(content_lines)
        objects = [
            "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
            "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
            (
                "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
            ),
            "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
            (
                f"5 0 obj << /Length {len(stream.encode('utf-8'))} >> stream\n"
                f"{stream}\nendstream\nendobj\n"
            ),
        ]

        pdf = "%PDF-1.4\n"
        offsets: list[int] = []
        for obj in objects:
            offsets.append(len(pdf.encode("utf-8")))
            pdf += obj
        xref_offset = len(pdf.encode("utf-8"))
        pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
        for offset in offsets:
            pdf += f"{offset:010d} 00000 n \n"
        pdf += (
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        )
        return pdf.encode("utf-8")

    async def _get_curriculum_or_404(self, curriculum_id: uuid.UUID) -> MenCurriculum:
        curriculum = await self.repo.get_curriculum(curriculum_id)
        if curriculum is None:
            raise NotFoundError("MEN curriculum not found", error_code="ERR-COMPLY-404")
        return curriculum

    async def _get_objective_or_404(
        self,
        objective_id: uuid.UUID,
        *,
        include_curriculum: bool = False,
    ) -> MenObjective:
        objective = await self.repo.get_objective(
            objective_id,
            include_curriculum=include_curriculum,
        )
        if objective is None:
            raise NotFoundError("MEN objective not found", error_code="ERR-COMPLY-404")
        return objective

    async def _get_report_or_404(
        self,
        report_id: uuid.UUID,
        auth: AuthContext,
    ) -> ComplianceReport:
        report = await self.repo.get_report(
            report_id,
            school_id=auth.school_id,
            include_curriculum=True,
        )
        if report is None:
            raise NotFoundError(
                "Compliance report not found", error_code="ERR-COMPLY-404"
            )
        return report

    async def _ensure_academic_year_or_404(
        self,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ) -> None:
        academic_year = await self.repo.get_academic_year(academic_year_id)
        if academic_year is None:
            raise NotFoundError("Academic year not found", error_code="ERR-COMPLY-404")
        verify_school_boundary(academic_year.school_id, auth)

    async def _ensure_course_or_404(
        self,
        course_id: uuid.UUID,
        auth: AuthContext,
    ) -> None:
        course = await self.repo.get_course(course_id)
        if course is None:
            raise NotFoundError("Course not found", error_code="ERR-COMPLY-404")
        verify_school_boundary(course.school_id, auth)

    async def _ensure_content_item_or_404(
        self,
        content_item_id: uuid.UUID,
        auth: AuthContext,
    ) -> None:
        content_item = await self.repo.get_content_item(content_item_id)
        if content_item is None:
            raise NotFoundError("Content item not found", error_code="ERR-COMPLY-404")
        if content_item.school_id is not None:
            verify_school_boundary(content_item.school_id, auth)

    async def _calculate_snapshot(
        self,
        *,
        school_id: uuid.UUID,
        curriculum_id: uuid.UUID,
    ) -> tuple[
        MenCurriculum, list[MenObjective], list[CurriculumMapping], list[str], float
    ]:
        curriculum = await self.repo.get_curriculum(curriculum_id)
        if curriculum is None:
            raise NotFoundError("MEN curriculum not found", error_code="ERR-COMPLY-404")
        objectives = await self.repo.list_objectives(
            curriculum_id=curriculum_id,
            include_curriculum=True,
        )
        mappings = await self.repo.list_mappings(
            school_id=school_id,
            curriculum_id=curriculum_id,
            include_objective=True,
        )
        mapped_objective_ids = {mapping.objective_id for mapping in mappings}
        total_objectives = len(objectives)
        mapped_objectives = len(mapped_objective_ids)
        unmapped_codes = [
            objective.code
            for objective in objectives
            if objective.id not in mapped_objective_ids
        ]
        compliance_percent = round(
            (mapped_objectives / total_objectives) * 100.0 if total_objectives else 0.0,
            2,
        )
        return curriculum, objectives, mappings, unmapped_codes, compliance_percent

    async def list_curricula(
        self,
        *,
        level: str | None = None,
        grade: str | None = None,
        subject: str | None = None,
        academic_year: str | None = None,
        is_active: bool | None = None,
    ) -> list[dict[str, Any]]:
        curricula = await self.repo.list_curricula(
            level=level,
            grade=grade,
            subject=subject,
            academic_year=academic_year,
            is_active=is_active,
        )
        return [self._curriculum_to_response(item) for item in curricula]

    async def create_curriculum(
        self,
        *,
        body: MenCurriculumCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_seed_role(auth)
        existing = await self.repo.get_curriculum_by_scope(
            level=body.level.strip(),
            grade=body.grade.strip(),
            subject=body.subject.strip(),
            academic_year=body.academic_year.strip(),
            version=body.version.strip(),
        )
        if existing is not None:
            raise ConflictError(
                "MEN curriculum already exists",
                error_code="ERR-COMPLY-409",
            )

        async with UnitOfWork(self.db) as uow:
            repo = ComplianceRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            curriculum = MenCurriculum(
                level=body.level,
                grade=body.grade,
                subject=body.subject,
                academic_year=body.academic_year,
                version=body.version,
                is_active=body.is_active,
            )
            created = await repo.create_curriculum(curriculum)
            response = self._curriculum_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="compliance.curriculum.create",
                outcome="success",
                target_type="men_curriculum",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                MenCurriculumCreated(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    curriculum_id=created.id,
                    subject=created.subject,
                    grade=created.grade,
                )
            )
            await uow.commit()
        return response

    async def list_objectives(
        self,
        *,
        curriculum_id: uuid.UUID,
        trimester: int | None = None,
    ) -> list[dict[str, Any]]:
        await self._get_curriculum_or_404(curriculum_id)
        objectives = await self.repo.list_objectives(
            curriculum_id=curriculum_id,
            trimester=trimester,
            include_curriculum=True,
        )
        return [self._objective_to_response(item) for item in objectives]

    async def create_objective(
        self,
        *,
        curriculum_id: uuid.UUID,
        body: MenObjectiveCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_seed_role(auth)
        await self._get_curriculum_or_404(curriculum_id)
        existing = await self.repo.get_objective_by_code(
            curriculum_id=curriculum_id,
            code=body.code.strip().upper().replace(" ", "-"),
        )
        if existing is not None:
            raise ConflictError(
                "MEN objective code already exists in this curriculum",
                error_code="ERR-COMPLY-409",
            )

        async with UnitOfWork(self.db) as uow:
            repo = ComplianceRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            objective = MenObjective(
                curriculum_id=curriculum_id,
                code=body.code,
                title_fr=body.title_fr,
                title_ar=body.title_ar,
                description_fr=body.description_fr,
                trimester=body.trimester,
                unit_number=body.unit_number,
                is_mandatory=body.is_mandatory,
                hours_recommended=body.hours_recommended,
                display_order=body.display_order,
            )
            created = await repo.create_objective(objective)
            hydrated_objective = await repo.get_objective(
                created.id, include_curriculum=True
            )
            if hydrated_objective is None:
                raise NotFoundError(
                    "MEN objective not found", error_code="ERR-COMPLY-404"
                )
            response = self._objective_to_response(hydrated_objective)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="compliance.objective.create",
                outcome="success",
                target_type="men_objective",
                target_id=hydrated_objective.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                MenObjectiveCreated(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    objective_id=hydrated_objective.id,
                    curriculum_id=hydrated_objective.curriculum_id,
                    code=hydrated_objective.code,
                )
            )
            await uow.commit()
        return response

    async def create_mapping(
        self,
        *,
        body: CurriculumMappingCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        await self._get_objective_or_404(
            body.objective_id,
            include_curriculum=True,
        )
        if body.course_id is None and body.content_item_id is None:
            raise ValidationError(
                "Mapping requires a course_id or content_item_id",
                error_code="ERR-COMPLY-422",
            )
        if body.course_id is not None:
            await self._ensure_course_or_404(body.course_id, auth)
        if body.content_item_id is not None:
            await self._ensure_content_item_or_404(body.content_item_id, auth)

        existing = await self.repo.find_mapping(
            school_id=auth.school_id,
            objective_id=body.objective_id,
            course_id=body.course_id,
            content_item_id=body.content_item_id,
        )
        if existing is not None:
            raise ConflictError(
                "This curriculum mapping already exists",
                error_code="ERR-COMPLY-409",
            )

        async with UnitOfWork(self.db) as uow:
            repo = ComplianceRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            mapping = CurriculumMapping(
                school_id=auth.school_id,
                objective_id=body.objective_id,
                course_id=body.course_id,
                content_item_id=body.content_item_id,
                mapped_by=auth.user_id,
                coverage_percent=body.coverage_percent,
                notes=body.notes,
            )
            created = await repo.create_mapping(mapping)
            hydrated_mapping = await repo.get_mapping(
                created.id,
                school_id=auth.school_id,
                include_objective=True,
            )
            if hydrated_mapping is None:
                raise NotFoundError(
                    "Curriculum mapping not found", error_code="ERR-COMPLY-404"
                )
            response = self._mapping_to_response(hydrated_mapping)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="compliance.mapping.create",
                outcome="success",
                target_type="curriculum_mapping",
                target_id=hydrated_mapping.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                CurriculumMapped(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    mapping_id=hydrated_mapping.id,
                    objective_id=hydrated_mapping.objective_id,
                    course_id=hydrated_mapping.course_id,
                    coverage_percent=hydrated_mapping.coverage_percent,
                )
            )
            await uow.commit()
        return response

    async def list_mappings(
        self,
        *,
        auth: AuthContext,
        curriculum_id: uuid.UUID | None = None,
        objective_id: uuid.UUID | None = None,
        course_id: uuid.UUID | None = None,
        content_item_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        mappings = await self.repo.list_mappings(
            school_id=auth.school_id,
            curriculum_id=curriculum_id,
            objective_id=objective_id,
            course_id=course_id,
            content_item_id=content_item_id,
            include_objective=True,
        )
        return [self._mapping_to_response(item) for item in mappings]

    async def delete_mapping(
        self,
        *,
        mapping_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> None:
        mapping = await self.repo.get_mapping(
            mapping_id,
            school_id=auth.school_id,
            include_objective=True,
        )
        if mapping is None:
            raise NotFoundError(
                "Curriculum mapping not found", error_code="ERR-COMPLY-404"
            )
        before = self._mapping_to_response(mapping)

        async with UnitOfWork(self.db) as uow:
            repo = ComplianceRepository(uow.session)
            audit = AuditService(uow.session)
            current = await repo.get_mapping(
                mapping_id,
                school_id=auth.school_id,
                include_objective=True,
            )
            if current is None:
                raise NotFoundError(
                    "Curriculum mapping not found",
                    error_code="ERR-COMPLY-404",
                )
            await repo.delete_mapping(current)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="compliance.mapping.delete",
                outcome="success",
                target_type="curriculum_mapping",
                target_id=mapping_id,
                entity_before=before,
                ip_address=ip_address,
            )
            await uow.commit()

    async def get_dashboard(
        self,
        *,
        auth: AuthContext,
        academic_year_id: uuid.UUID | None = None,
        level: str | None = None,
        grade: str | None = None,
        subject: str | None = None,
    ) -> dict[str, Any]:
        if academic_year_id is not None:
            await self._ensure_academic_year_or_404(academic_year_id, auth)
        curricula = await self.repo.list_curricula(
            level=level,
            grade=grade,
            subject=subject,
            is_active=True,
        )
        items: list[ComplianceDashboardItemResponse] = []
        total_objectives = 0
        mapped_objectives = 0

        for curriculum in curricula:
            (
                _,
                objectives,
                _,
                unmapped_codes,
                compliance_percent,
            ) = await self._calculate_snapshot(
                school_id=auth.school_id,
                curriculum_id=curriculum.id,
            )
            total = len(objectives)
            mapped = total - len(unmapped_codes)
            total_objectives += total
            mapped_objectives += mapped
            items.append(
                ComplianceDashboardItemResponse(
                    curriculum_id=str(curriculum.id),
                    level=curriculum.level,
                    grade=curriculum.grade,
                    subject=curriculum.subject,
                    academic_year=curriculum.academic_year,
                    total_objectives=total,
                    mapped_objectives=mapped,
                    unmapped_objectives=len(unmapped_codes),
                    compliance_percent=compliance_percent,
                )
            )

        overall_percent = round(
            (mapped_objectives / total_objectives) * 100.0 if total_objectives else 0.0,
            2,
        )
        return ComplianceDashboardResponse(
            school_id=str(auth.school_id),
            academic_year_id=str(academic_year_id)
            if academic_year_id is not None
            else None,
            curriculum_count=len(items),
            total_objectives=total_objectives,
            mapped_objectives=mapped_objectives,
            overall_compliance_percent=overall_percent,
            items=items,
        ).model_dump()

    async def generate_report(
        self,
        *,
        body: ComplianceReportGenerateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        await self._ensure_academic_year_or_404(body.academic_year_id, auth)
        (
            curriculum,
            objectives,
            _,
            unmapped_codes,
            compliance_percent,
        ) = await self._calculate_snapshot(
            school_id=auth.school_id,
            curriculum_id=body.curriculum_id,
        )
        mapped_objectives = len(objectives) - len(unmapped_codes)

        async with UnitOfWork(self.db) as uow:
            repo = ComplianceRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            report = ComplianceReport(
                school_id=auth.school_id,
                curriculum_id=curriculum.id,
                generated_by=auth.user_id,
                total_objectives=len(objectives),
                mapped_objectives=mapped_objectives,
                compliance_percent=compliance_percent,
                unmapped_objectives=unmapped_codes,
                pdf_url=None,
                academic_year_id=body.academic_year_id,
            )
            created = await repo.create_report(report)
            created.pdf_url = self._report_url(created.id)
            created = await repo.save_report(created)
            hydrated_report = await repo.get_report(
                created.id,
                school_id=auth.school_id,
                include_curriculum=True,
            )
            if hydrated_report is None:
                raise NotFoundError(
                    "Compliance report not found", error_code="ERR-COMPLY-404"
                )
            response = self._report_to_response(hydrated_report)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="compliance.report.generate",
                outcome="success",
                target_type="compliance_report",
                target_id=hydrated_report.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                ComplianceReportGenerated(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    report_id=hydrated_report.id,
                    curriculum_id=hydrated_report.curriculum_id,
                    compliance_percent=float(hydrated_report.compliance_percent),
                )
            )
            await uow.commit()
        return response

    async def list_reports(
        self,
        *,
        auth: AuthContext,
        curriculum_id: uuid.UUID | None = None,
        academic_year_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        if academic_year_id is not None:
            await self._ensure_academic_year_or_404(academic_year_id, auth)
        reports = await self.repo.list_reports(
            school_id=auth.school_id,
            curriculum_id=curriculum_id,
            academic_year_id=academic_year_id,
        )
        return [self._report_to_response(item) for item in reports]

    async def get_report(
        self,
        *,
        report_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        report = await self._get_report_or_404(report_id, auth)
        return self._report_to_response(report)

    async def download_pdf(
        self,
        *,
        report_id: uuid.UUID,
        auth: AuthContext,
    ) -> bytes:
        report = await self._get_report_or_404(report_id, auth)
        curriculum = report.curriculum or await self._get_curriculum_or_404(
            report.curriculum_id
        )
        lines = [
            "MEN Compliance Report",
            f"School ID: {report.school_id}",
            f"Subject: {curriculum.subject}",
            f"Grade: {curriculum.grade}",
            f"Compliance: {float(report.compliance_percent):.2f}%",
            f"Mapped objectives: {report.mapped_objectives}/{report.total_objectives}",
        ]
        for code in list(report.unmapped_objectives or [])[:12]:
            lines.append(f"Unmapped: {code}")
        return self._build_minimal_pdf(lines)

    async def seed_reference_curricula(
        self,
        *,
        auth: AuthContext | None = None,
        ip_address: str | None = None,
    ) -> dict[str, int]:
        if auth is not None:
            self._ensure_seed_role(auth)

        async with UnitOfWork(self.db) as uow:
            repo = ComplianceRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            curricula_created = 0
            objectives_created = 0

            for payload in DEFAULT_CURRICULA:
                curriculum = await repo.get_curriculum_by_scope(
                    level=payload["level"],
                    grade=payload["grade"],
                    subject=payload["subject"],
                    academic_year=payload["academic_year"],
                    version=payload["version"],
                )
                if curriculum is None:
                    curriculum = MenCurriculum(
                        level=payload["level"],
                        grade=payload["grade"],
                        subject=payload["subject"],
                        academic_year=payload["academic_year"],
                        version=payload["version"],
                        is_active=True,
                    )
                    curriculum = await repo.create_curriculum(curriculum)
                    curricula_created += 1

                for objective_payload in payload["objectives"]:
                    existing_objective = await repo.get_objective_by_code(
                        curriculum_id=curriculum.id,
                        code=objective_payload["code"],
                    )
                    if existing_objective is not None:
                        continue
                    objective = MenObjective(
                        curriculum_id=curriculum.id,
                        **objective_payload,
                    )
                    await repo.create_objective(objective)
                    objectives_created += 1

            await dispatcher.dispatch(
                MenCurriculumSeeded(
                    school_id=auth.school_id if auth is not None else None,
                    actor_id=auth.user_id if auth is not None else None,
                    curriculum_count=curricula_created,
                    objective_count=objectives_created,
                )
            )
            if auth is not None:
                await audit.log_event(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    action_type="compliance.seed",
                    outcome="success",
                    target_type="men_curriculum_seed",
                    entity_after={
                        "curricula_created": curricula_created,
                        "objectives_created": objectives_created,
                    },
                    ip_address=ip_address,
                )
            await uow.commit()

        return {
            "curricula_created": curricula_created,
            "objectives_created": objectives_created,
        }


async def seed_men_reference_data(db: AsyncSession) -> dict[str, int]:
    """Convenience wrapper used by scripts and tests."""

    service = ComplianceService(db)
    return await service.seed_reference_curricula()


__all__ = ["ComplianceService", "seed_men_reference_data"]
