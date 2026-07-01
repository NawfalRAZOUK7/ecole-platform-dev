"""Service layer for life-skills passport workflows."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.permissions import ADM, DIR, PAR, STD, SUP, SYS, TCH
from app.core.unit_of_work import UnitOfWork
from app.domain.events.skill_passport import (
    SkillDimensionCreated,
    SkillMilestoneCreated,
    SkillPassportGenerated,
    SkillProgressEvaluated,
)
from app.models.erp import AcademicYear, Class
from app.models.iam import User
from app.models.skill_passport import (
    SkillDimension,
    SkillMilestone,
    SkillPassport,
    SkillProgress,
    SkillProgressStatus,
)
from app.repositories.academic_skill_passport import SkillPassportRepository
from app.schemas.academic.skill_passport import (
    SkillClassAnalyticsResponse,
    SkillDimensionAnalyticsResponse,
    SkillDimensionCreateRequest,
    SkillDimensionResponse,
    SkillDimensionUpdateRequest,
    SkillEvaluationResponse,
    SkillLeaderboardEntryResponse,
    SkillMilestoneCreateRequest,
    SkillMilestoneResponse,
    SkillMilestoneUpdateRequest,
    SkillPassportResponse,
    SkillProgressResponse,
    SkillSchoolAnalyticsResponse,
)
from app.services.platform.audit import AuditService
from app.services.communication.event_dispatcher import EventDispatcher

ADMIN_ROLES = {ADM, SUP, SYS}
STAFF_ROLES = ADMIN_ROLES | {DIR, TCH}
METRIC_ALIASES: dict[str, str] = {
    "activity_sessions_completed": "activity_sessions_completed",
    "sessions_completed": "activity_sessions_completed",
    "completed_activity_sessions": "activity_sessions_completed",
    "content_items_completed": "content_items_completed",
    "modules_completed": "content_items_completed",
    "modules_without_help": "content_items_completed",
    "assignments_submitted": "assignments_submitted",
    "submitted_assignments": "assignments_submitted",
    "submissions_on_time": "submissions_on_time",
    "on_time_submissions": "submissions_on_time",
    "quiz_attempts": "quiz_attempts",
    "quiz_attempts_completed": "quiz_attempts",
    "average_quiz_score": "average_quiz_score",
    "avg_quiz_score": "average_quiz_score",
    "activity_types_completed": "activity_types_completed",
}


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value is not None else None


class _SkillServiceBase:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SkillPassportRepository(db)
        self.audit = AuditService(db)
        self._dispatcher = EventDispatcher(db)

    def _ensure_admin_role(self, auth: AuthContext) -> None:
        if auth.role not in ADMIN_ROLES:
            raise AuthorizationError(
                "Only administrators can manage the skills framework",
                error_code="ERR-SKILL-403",
            )

    def _ensure_staff_role(self, auth: AuthContext) -> None:
        if auth.role not in STAFF_ROLES:
            raise AuthorizationError(
                "Only school staff can evaluate life skills",
                error_code="ERR-SKILL-403",
            )

    async def _get_student_or_404(
        self,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> User:
        student = await self.repo.get_user(student_id)
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-SKILL-404")
        verify_school_boundary(student.school_id, auth)
        return student

    async def _ensure_student_access(
        self,
        student_id: uuid.UUID,
        auth: AuthContext,
    ) -> User:
        student = await self._get_student_or_404(student_id, auth)
        if auth.role in STAFF_ROLES:
            return student
        if auth.role == STD and auth.user_id == student_id:
            return student
        if auth.role == PAR and await self.repo.is_parent_of_student(
            parent_id=auth.user_id,
            student_id=student_id,
            school_id=auth.school_id,
        ):
            return student
        raise AuthorizationError(
            "You do not have access to this student's skill passport",
            error_code="ERR-SKILL-403",
        )

    async def _get_academic_year_or_404(
        self,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ) -> AcademicYear:
        academic_year = await self.repo.get_academic_year(academic_year_id)
        if academic_year is None:
            raise NotFoundError("Academic year not found", error_code="ERR-SKILL-404")
        verify_school_boundary(academic_year.school_id, auth)
        return academic_year

    async def _get_class_or_404(
        self,
        class_id: uuid.UUID,
        auth: AuthContext,
    ) -> Class:
        school_class = await self.repo.get_class(class_id)
        if school_class is None:
            raise NotFoundError("Class not found", error_code="ERR-SKILL-404")
        verify_school_boundary(school_class.school_id, auth)
        return school_class

    async def _get_dimension_or_404(self, dimension_id: uuid.UUID) -> SkillDimension:
        dimension = await self.repo.get_dimension(dimension_id)
        if dimension is None:
            raise NotFoundError("Skill dimension not found", error_code="ERR-SKILL-404")
        return dimension

    async def _get_milestone_or_404(
        self,
        milestone_id: uuid.UUID,
    ) -> SkillMilestone:
        milestone = await self.repo.get_milestone(milestone_id, include_dimension=True)
        if milestone is None:
            raise NotFoundError("Skill milestone not found", error_code="ERR-SKILL-404")
        return milestone

    async def _get_passport_record_or_404(
        self,
        passport_id: uuid.UUID,
        auth: AuthContext,
    ) -> SkillPassport:
        passport = await self.repo.get_passport_by_id(
            passport_id, school_id=auth.school_id
        )
        if passport is None:
            raise NotFoundError("Skill passport not found", error_code="ERR-SKILL-404")
        await self._ensure_student_access(passport.student_id, auth)
        return passport

    def _dimension_to_response(self, dimension: SkillDimension) -> dict[str, Any]:
        return SkillDimensionResponse(
            id=str(dimension.id),
            code=dimension.code,
            name_fr=dimension.name_fr,
            name_ar=dimension.name_ar,
            name_en=dimension.name_en,
            description_fr=dimension.description_fr,
            icon=dimension.icon,
            display_order=dimension.display_order,
            is_active=dimension.is_active,
            created_at=_iso(dimension.created_at) or "",
            updated_at=_iso(dimension.updated_at),
        ).model_dump()

    def _milestone_to_response(self, milestone: SkillMilestone) -> dict[str, Any]:
        return SkillMilestoneResponse(
            id=str(milestone.id),
            dimension_id=str(milestone.dimension_id),
            dimension_code=milestone.dimension.code
            if milestone.dimension is not None
            else None,
            code=milestone.code,
            name_fr=milestone.name_fr,
            name_ar=milestone.name_ar,
            level=milestone.level,
            rule_config=dict(milestone.rule_config or {}),
            badge_icon=milestone.badge_icon,
            is_active=milestone.is_active,
            created_at=_iso(milestone.created_at) or "",
            updated_at=_iso(milestone.updated_at),
        ).model_dump()

    def _progress_to_response(self, progress: SkillProgress) -> dict[str, Any]:
        milestone = progress.milestone
        dimension = milestone.dimension if milestone is not None else None
        return SkillProgressResponse(
            id=str(progress.id),
            student_id=str(progress.student_id),
            school_id=str(progress.school_id),
            milestone_id=str(progress.milestone_id),
            milestone_code=milestone.code if milestone is not None else None,
            dimension_id=str(dimension.id) if dimension is not None else None,
            dimension_code=dimension.code if dimension is not None else None,
            unlocked_at=_iso(progress.unlocked_at),
            current_value=float(progress.current_value),
            status=progress.status,
            evidence=dict(progress.evidence) if progress.evidence is not None else None,
            academic_year_id=str(progress.academic_year_id),
            created_at=_iso(progress.created_at) or "",
            updated_at=_iso(progress.updated_at),
        ).model_dump()

    def _passport_to_response(
        self,
        passport: SkillPassport,
        *,
        progress_items: list[SkillProgress] | None = None,
    ) -> dict[str, Any]:
        return SkillPassportResponse(
            id=str(passport.id),
            student_id=str(passport.student_id),
            school_id=str(passport.school_id),
            academic_year_id=str(passport.academic_year_id),
            generated_at=_iso(passport.generated_at) or "",
            pdf_url=passport.pdf_url,
            total_milestones=passport.total_milestones,
            unlocked_milestones=passport.unlocked_milestones,
            overall_score=float(passport.overall_score),
            created_at=_iso(passport.created_at) or "",
            updated_at=_iso(passport.updated_at),
            progress_items=[
                SkillProgressResponse.model_validate(self._progress_to_response(item))
                for item in (progress_items or [])
            ],
        ).model_dump()

    def _normalize_metric_config(
        self, rule_config: dict[str, Any]
    ) -> tuple[str, float, int]:
        raw_metric = (
            str(rule_config.get("metric", "content_items_completed")).strip().lower()
        )
        metric = METRIC_ALIASES.get(raw_metric)
        if metric is None:
            raise ValidationError(
                f"Unsupported skill metric: {raw_metric}",
                error_code="ERR-SKILL-422",
            )
        threshold_raw = rule_config.get("threshold", 1)
        threshold = float(1 if threshold_raw is None else threshold_raw)
        if threshold <= 0:
            raise ValidationError(
                "Skill milestone threshold must be greater than zero",
                error_code="ERR-SKILL-422",
            )
        period_days_raw = rule_config.get("period_days", 30)
        period_days = int(30 if period_days_raw is None else period_days_raw)
        if period_days <= 0:
            raise ValidationError(
                "Skill milestone period_days must be greater than zero",
                error_code="ERR-SKILL-422",
            )
        return metric, threshold, period_days

    async def _resolve_metric_value(
        self,
        repo: SkillPassportRepository,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        metric: str,
        since: datetime,
    ) -> float:
        if metric == "activity_sessions_completed":
            return float(
                await repo.count_completed_activity_sessions(
                    student_id=student_id,
                    since=since,
                )
            )
        if metric == "content_items_completed":
            return float(
                await repo.count_completed_content_items(
                    student_id=student_id,
                    since=since,
                )
            )
        if metric == "assignments_submitted":
            return float(
                await repo.count_submitted_assignments(
                    student_id=student_id,
                    school_id=school_id,
                    since=since,
                    on_time_only=False,
                )
            )
        if metric == "submissions_on_time":
            return float(
                await repo.count_submitted_assignments(
                    student_id=student_id,
                    school_id=school_id,
                    since=since,
                    on_time_only=True,
                )
            )
        if metric == "quiz_attempts":
            return float(
                await repo.count_quiz_attempts(
                    student_id=student_id,
                    school_id=school_id,
                    since=since,
                )
            )
        if metric == "average_quiz_score":
            return float(
                await repo.average_quiz_score_percent(
                    student_id=student_id,
                    school_id=school_id,
                    since=since,
                )
            )
        if metric == "activity_types_completed":
            return float(
                await repo.count_activity_types_completed(
                    student_id=student_id,
                    since=since,
                )
            )
        raise ValidationError("Unsupported skill metric", error_code="ERR-SKILL-422")

    async def _analyze_metrics(
        self,
        repo: SkillPassportRepository,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        horizon_days: int = 30,
    ) -> dict[str, float]:
        since = datetime.now(timezone.utc) - timedelta(days=horizon_days)
        metrics = {}
        for metric in sorted(set(METRIC_ALIASES.values())):
            metrics[metric] = await self._resolve_metric_value(
                repo,
                student_id=student_id,
                school_id=school_id,
                metric=metric,
                since=since,
            )
        return metrics

    async def _evaluate_student_records(
        self,
        repo: SkillPassportRepository,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        actor_id: uuid.UUID,
        dispatcher: EventDispatcher | None = None,
    ) -> tuple[list[SkillProgress], dict[str, float], int, int, float]:
        milestones = await repo.list_milestones(is_active=True, include_dimension=True)
        existing_records = await repo.list_progress(
            school_id=school_id,
            academic_year_id=academic_year_id,
            student_id=student_id,
            include_milestone=True,
        )
        existing_by_milestone = {item.milestone_id: item for item in existing_records}
        metrics = await self._analyze_metrics(
            repo,
            student_id=student_id,
            school_id=school_id,
        )
        now = datetime.now(timezone.utc)
        evaluated_records: list[SkillProgress] = []
        unlocked_count = 0

        for milestone in milestones:
            metric, threshold, period_days = self._normalize_metric_config(
                dict(milestone.rule_config or {})
            )
            since = now - timedelta(days=period_days)
            actual_value = await self._resolve_metric_value(
                repo,
                student_id=student_id,
                school_id=school_id,
                metric=metric,
                since=since,
            )
            completion_percent = round(
                min(100.0, (actual_value / threshold) * 100.0), 2
            )
            if actual_value >= threshold:
                status = SkillProgressStatus.UNLOCKED.value
                unlocked_at = now
                unlocked_count += 1
            elif actual_value > 0:
                status = SkillProgressStatus.IN_PROGRESS.value
                unlocked_at = None
            else:
                status = SkillProgressStatus.LOCKED.value
                unlocked_at = None

            evidence = {
                "metric": metric,
                "threshold": threshold,
                "actual_value": round(actual_value, 2),
                "period_days": period_days,
            }

            progress = existing_by_milestone.get(milestone.id)
            if progress is None:
                progress = SkillProgress(
                    student_id=student_id,
                    school_id=school_id,
                    milestone_id=milestone.id,
                    academic_year_id=academic_year_id,
                    current_value=completion_percent,
                    status=status,
                    evidence=evidence,
                    unlocked_at=unlocked_at,
                )
                progress = await repo.create_progress(progress)
            else:
                progress.current_value = completion_percent
                progress.status = status
                progress.evidence = evidence
                if status == SkillProgressStatus.UNLOCKED.value:
                    progress.unlocked_at = progress.unlocked_at or unlocked_at
                progress = await repo.save_progress(progress)
            progress.milestone = milestone
            progress.milestone.dimension = milestone.dimension
            evaluated_records.append(progress)

            if dispatcher is not None:
                await dispatcher.dispatch(
                    SkillProgressEvaluated(
                        school_id=school_id,
                        actor_id=actor_id,
                        skill_progress_id=progress.id,
                        student_id=student_id,
                        milestone_id=milestone.id,
                        status=status,
                    )
                )

        total_milestones = len(milestones)
        overall_score = round(
            (unlocked_count / total_milestones) * 100.0 if total_milestones else 0.0,
            2,
        )
        return (
            evaluated_records,
            metrics,
            total_milestones,
            unlocked_count,
            overall_score,
        )

    def _passport_url(self, passport_id: uuid.UUID) -> str:
        return f"/generated/skill-passports/{passport_id}.pdf"

    def _build_dimension_summaries(
        self,
        *,
        dimensions: list[SkillDimension],
        milestones: list[SkillMilestone],
        progress_items: list[SkillProgress],
    ) -> list[dict[str, Any]]:
        milestone_count_by_dimension: dict[uuid.UUID, int] = defaultdict(int)
        unlocked_count_by_dimension: dict[uuid.UUID, int] = defaultdict(int)
        progress_values_by_dimension: dict[uuid.UUID, list[float]] = defaultdict(list)

        for milestone in milestones:
            milestone_count_by_dimension[milestone.dimension_id] += 1

        for progress in progress_items:
            if progress.milestone is None or progress.milestone.dimension is None:
                continue
            dimension_id = progress.milestone.dimension.id
            progress_values_by_dimension[dimension_id].append(
                float(progress.current_value)
            )
            if progress.status == SkillProgressStatus.UNLOCKED.value:
                unlocked_count_by_dimension[dimension_id] += 1

        summaries: list[dict[str, Any]] = []
        for dimension in dimensions:
            values = progress_values_by_dimension.get(dimension.id, [])
            summaries.append(
                SkillDimensionAnalyticsResponse(
                    dimension_id=str(dimension.id),
                    code=dimension.code,
                    name_fr=dimension.name_fr,
                    milestone_count=milestone_count_by_dimension.get(dimension.id, 0),
                    unlocked_count=unlocked_count_by_dimension.get(dimension.id, 0),
                    average_progress=round(sum(values) / len(values), 2)
                    if values
                    else 0.0,
                ).model_dump()
            )
        return summaries

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


class SkillPassportService(_SkillServiceBase):
    """Business logic for life-skills dimensions, milestones, progress, passports, and analytics."""

    async def list_dimensions(
        self,
        *,
        is_active: bool | None = None,
    ) -> list[dict[str, Any]]:
        dimensions = await self.repo.list_dimensions(is_active=is_active)
        return [self._dimension_to_response(item) for item in dimensions]

    async def create_dimension(
        self,
        *,
        body: SkillDimensionCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_admin_role(auth)
        existing = await self.repo.get_dimension_by_code(
            body.code.strip().lower().replace(" ", "_")
        )
        if existing is not None:
            raise ConflictError(
                "Skill dimension code already exists",
                error_code="ERR-SKILL-409",
            )

        async with UnitOfWork(self.db) as uow:
            repo = SkillPassportRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            dimension = SkillDimension(
                code=body.code,
                name_fr=body.name_fr,
                name_ar=body.name_ar,
                name_en=body.name_en,
                description_fr=body.description_fr,
                icon=body.icon,
                display_order=body.display_order,
                is_active=body.is_active,
            )
            created = await repo.create_dimension(dimension)
            response = self._dimension_to_response(created)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="skill.dimension.create",
                outcome="success",
                target_type="skill_dimension",
                target_id=created.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                SkillDimensionCreated(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    skill_dimension_id=created.id,
                    code=created.code,
                )
            )
            await uow.commit()
        return response

    async def update_dimension(
        self,
        *,
        dimension_id: uuid.UUID,
        body: SkillDimensionUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_admin_role(auth)
        dimension = await self._get_dimension_or_404(dimension_id)
        if body.code is not None:
            existing = await self.repo.get_dimension_by_code(
                body.code.strip().lower().replace(" ", "_")
            )
            if existing is not None and existing.id != dimension_id:
                raise ConflictError(
                    "Skill dimension code already exists",
                    error_code="ERR-SKILL-409",
                )
        before = self._dimension_to_response(dimension)

        async with UnitOfWork(self.db) as uow:
            repo = SkillPassportRepository(uow.session)
            audit = AuditService(uow.session)
            current = await repo.get_dimension(dimension_id)
            if current is None:
                raise NotFoundError(
                    "Skill dimension not found", error_code="ERR-SKILL-404"
                )
            for field in (
                "code",
                "name_fr",
                "name_ar",
                "name_en",
                "description_fr",
                "icon",
                "display_order",
                "is_active",
            ):
                value = getattr(body, field)
                if value is not None:
                    setattr(current, field, value)
            saved = await repo.save_dimension(current)
            response = self._dimension_to_response(saved)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="skill.dimension.update",
                outcome="success",
                target_type="skill_dimension",
                target_id=saved.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def list_milestones(
        self,
        *,
        dimension_id: uuid.UUID | None = None,
        is_active: bool | None = None,
    ) -> list[dict[str, Any]]:
        milestones = await self.repo.list_milestones(
            dimension_id=dimension_id,
            is_active=is_active,
            include_dimension=True,
        )
        return [self._milestone_to_response(item) for item in milestones]

    async def create_milestone(
        self,
        *,
        body: SkillMilestoneCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_admin_role(auth)
        await self._get_dimension_or_404(body.dimension_id)
        existing = await self.repo.get_milestone_by_code(
            dimension_id=body.dimension_id,
            code=body.code.strip().lower().replace(" ", "_"),
        )
        if existing is not None:
            raise ConflictError(
                "Skill milestone code already exists in this dimension",
                error_code="ERR-SKILL-409",
            )
        self._normalize_metric_config(dict(body.rule_config))

        async with UnitOfWork(self.db) as uow:
            repo = SkillPassportRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            milestone = SkillMilestone(
                dimension_id=body.dimension_id,
                code=body.code,
                name_fr=body.name_fr,
                name_ar=body.name_ar,
                level=body.level,
                rule_config=dict(body.rule_config),
                badge_icon=body.badge_icon,
                is_active=body.is_active,
            )
            created = await repo.create_milestone(milestone)
            hydrated_milestone = await repo.get_milestone(
                created.id, include_dimension=True
            )
            if hydrated_milestone is None:
                raise NotFoundError(
                    "Skill milestone not found", error_code="ERR-SKILL-404"
                )
            response = self._milestone_to_response(hydrated_milestone)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="skill.milestone.create",
                outcome="success",
                target_type="skill_milestone",
                target_id=hydrated_milestone.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                SkillMilestoneCreated(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    skill_milestone_id=hydrated_milestone.id,
                    dimension_id=hydrated_milestone.dimension_id,
                    code=hydrated_milestone.code,
                )
            )
            await uow.commit()
        return response

    async def update_milestone(
        self,
        *,
        milestone_id: uuid.UUID,
        body: SkillMilestoneUpdateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_admin_role(auth)
        milestone = await self._get_milestone_or_404(milestone_id)
        if body.code is not None:
            existing = await self.repo.get_milestone_by_code(
                dimension_id=milestone.dimension_id,
                code=body.code.strip().lower().replace(" ", "_"),
            )
            if existing is not None and existing.id != milestone_id:
                raise ConflictError(
                    "Skill milestone code already exists in this dimension",
                    error_code="ERR-SKILL-409",
                )
        if body.rule_config is not None:
            self._normalize_metric_config(dict(body.rule_config))
        before = self._milestone_to_response(milestone)

        async with UnitOfWork(self.db) as uow:
            repo = SkillPassportRepository(uow.session)
            audit = AuditService(uow.session)
            current = await repo.get_milestone(milestone_id, include_dimension=True)
            if current is None:
                raise NotFoundError(
                    "Skill milestone not found", error_code="ERR-SKILL-404"
                )
            for field in (
                "code",
                "name_fr",
                "name_ar",
                "level",
                "badge_icon",
                "is_active",
            ):
                value = getattr(body, field)
                if value is not None:
                    setattr(current, field, value)
            if body.rule_config is not None:
                current.rule_config = dict(body.rule_config)
            saved = await repo.save_milestone(current)
            hydrated_milestone = await repo.get_milestone(
                saved.id, include_dimension=True
            )
            if hydrated_milestone is None:
                raise NotFoundError(
                    "Skill milestone not found", error_code="ERR-SKILL-404"
                )
            response = self._milestone_to_response(hydrated_milestone)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="skill.milestone.update",
                outcome="success",
                target_type="skill_milestone",
                target_id=hydrated_milestone.id,
                entity_before=before,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def get_student_progress(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ) -> list[dict[str, Any]]:
        await self._ensure_student_access(student_id, auth)
        await self._get_academic_year_or_404(academic_year_id, auth)
        progress_items = await self.repo.list_progress(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
            student_id=student_id,
            include_milestone=True,
        )
        return [self._progress_to_response(item) for item in progress_items]

    async def analyze_activity_logs(
        self,
        *,
        student_id: uuid.UUID,
        auth: AuthContext,
        horizon_days: int = 30,
    ) -> dict[str, float]:
        await self._ensure_student_access(student_id, auth)
        return await self._analyze_metrics(
            self.repo,
            student_id=student_id,
            school_id=auth.school_id,
            horizon_days=horizon_days,
        )

    async def evaluate_student(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_staff_role(auth)
        await self._get_student_or_404(student_id, auth)
        await self._get_academic_year_or_404(academic_year_id, auth)

        async with UnitOfWork(self.db) as uow:
            repo = SkillPassportRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            (
                progress_items,
                metrics,
                total_milestones,
                unlocked_milestones,
                overall_score,
            ) = await self._evaluate_student_records(
                repo,
                student_id=student_id,
                school_id=auth.school_id,
                academic_year_id=academic_year_id,
                actor_id=auth.user_id,
                dispatcher=dispatcher,
            )
            response = SkillEvaluationResponse(
                student_id=str(student_id),
                school_id=str(auth.school_id),
                academic_year_id=str(academic_year_id),
                evaluated_at=_iso(datetime.now(timezone.utc)) or "",
                total_milestones=total_milestones,
                unlocked_milestones=unlocked_milestones,
                overall_score=overall_score,
                metrics={key: round(value, 2) for key, value in metrics.items()},
                progress_items=[
                    SkillProgressResponse.model_validate(
                        self._progress_to_response(item)
                    )
                    for item in progress_items
                ],
            ).model_dump()
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="skill.progress.evaluate",
                outcome="success",
                target_type="student",
                target_id=student_id,
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def get_passport(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        await self._ensure_student_access(student_id, auth)
        await self._get_academic_year_or_404(academic_year_id, auth)
        passport = await self.repo.get_passport(
            student_id=student_id,
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
        )
        if passport is None:
            if auth.role in STAFF_ROLES:
                return await self.generate_passport(
                    student_id=student_id,
                    academic_year_id=academic_year_id,
                    auth=auth,
                )
            raise NotFoundError(
                "Skill passport has not been generated yet",
                error_code="ERR-SKILL-404",
            )
        progress_items = await self.repo.list_progress(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
            student_id=student_id,
            include_milestone=True,
        )
        return self._passport_to_response(passport, progress_items=progress_items)

    async def generate_passport(
        self,
        *,
        student_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_staff_role(auth)
        await self._get_student_or_404(student_id, auth)
        await self._get_academic_year_or_404(academic_year_id, auth)

        async with UnitOfWork(self.db) as uow:
            repo = SkillPassportRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)
            (
                progress_items,
                _,
                total_milestones,
                unlocked_milestones,
                overall_score,
            ) = await self._evaluate_student_records(
                repo,
                student_id=student_id,
                school_id=auth.school_id,
                academic_year_id=academic_year_id,
                actor_id=auth.user_id,
                dispatcher=dispatcher,
            )

            passport = await repo.get_passport(
                student_id=student_id,
                school_id=auth.school_id,
                academic_year_id=academic_year_id,
            )
            now = datetime.now(timezone.utc)
            if passport is None:
                passport = SkillPassport(
                    student_id=student_id,
                    school_id=auth.school_id,
                    academic_year_id=academic_year_id,
                    generated_at=now,
                    total_milestones=total_milestones,
                    unlocked_milestones=unlocked_milestones,
                    overall_score=overall_score,
                    pdf_url=None,
                )
                passport = await repo.create_passport(passport)
            passport.generated_at = now
            passport.total_milestones = total_milestones
            passport.unlocked_milestones = unlocked_milestones
            passport.overall_score = overall_score
            passport.pdf_url = self._passport_url(passport.id)
            passport = await repo.save_passport(passport)

            response = self._passport_to_response(
                passport, progress_items=progress_items
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="skill.passport.generate",
                outcome="success",
                target_type="skill_passport",
                target_id=passport.id,
                entity_after=response,
                ip_address=ip_address,
            )
            await dispatcher.dispatch(
                SkillPassportGenerated(
                    school_id=auth.school_id,
                    actor_id=auth.user_id,
                    skill_passport_id=passport.id,
                    student_id=student_id,
                    academic_year_id=academic_year_id,
                    overall_score=overall_score,
                )
            )
            await uow.commit()
        return response

    async def generate_pdf(
        self,
        *,
        passport_id: uuid.UUID,
        auth: AuthContext,
    ) -> str:
        passport = await self._get_passport_record_or_404(passport_id, auth)
        if passport.pdf_url:
            return passport.pdf_url

        async with UnitOfWork(self.db) as uow:
            repo = SkillPassportRepository(uow.session)
            current = await repo.get_passport_by_id(
                passport_id, school_id=auth.school_id
            )
            if current is None:
                raise NotFoundError(
                    "Skill passport not found", error_code="ERR-SKILL-404"
                )
            current.pdf_url = self._passport_url(current.id)
            saved = await repo.save_passport(current)
            await uow.commit()
        return saved.pdf_url or self._passport_url(saved.id)

    async def download_pdf(
        self,
        *,
        passport_id: uuid.UUID,
        auth: AuthContext,
    ) -> bytes:
        passport = await self._get_passport_record_or_404(passport_id, auth)
        student = await self._ensure_student_access(passport.student_id, auth)
        progress_items = await self.repo.list_progress(
            school_id=passport.school_id,
            academic_year_id=passport.academic_year_id,
            student_id=passport.student_id,
            include_milestone=True,
        )
        lines = [
            "Life Skills Passport",
            f"Student ID: {student.id}",
            f"Academic year: {passport.academic_year_id}",
            f"Overall score: {float(passport.overall_score):.2f}%",
            f"Unlocked milestones: {passport.unlocked_milestones}/{passport.total_milestones}",
        ]
        for progress in progress_items[:12]:
            milestone_code = (
                progress.milestone.code
                if progress.milestone is not None
                else str(progress.milestone_id)
            )
            lines.append(
                f"{milestone_code}: {progress.status} ({float(progress.current_value):.2f}%)"
            )
        return self._build_minimal_pdf(lines)

    async def class_analytics(
        self,
        *,
        class_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        self._ensure_staff_role(auth)
        await self._get_class_or_404(class_id, auth)
        await self._get_academic_year_or_404(academic_year_id, auth)

        student_ids = set(
            await self.repo.list_class_student_ids(
                class_id=class_id, school_id=auth.school_id
            )
        )
        progress_items = await self.repo.list_progress(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
            student_ids=student_ids,
            include_milestone=True,
        )
        passports = await self.repo.list_passports(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
            student_ids=student_ids,
        )
        dimensions = await self.repo.list_dimensions(is_active=True)
        milestones = await self.repo.list_milestones(
            is_active=True, include_dimension=True
        )

        active_milestone_count = len(milestones)
        student_count = len(student_ids)
        progress_record_count = len(progress_items)
        unlocked_record_count = sum(
            1
            for item in progress_items
            if item.status == SkillProgressStatus.UNLOCKED.value
        )
        possible_records = student_count * active_milestone_count
        average_overall_score = round(
            (unlocked_record_count / possible_records) * 100.0
            if possible_records
            else 0.0,
            2,
        )

        return SkillClassAnalyticsResponse(
            class_id=str(class_id),
            school_id=str(auth.school_id),
            academic_year_id=str(academic_year_id),
            student_count=student_count,
            passport_count=len(passports),
            active_milestone_count=active_milestone_count,
            progress_record_count=progress_record_count,
            unlocked_record_count=unlocked_record_count,
            average_overall_score=average_overall_score,
            dimension_summaries=[
                SkillDimensionAnalyticsResponse.model_validate(item)
                for item in self._build_dimension_summaries(
                    dimensions=dimensions,
                    milestones=milestones,
                    progress_items=progress_items,
                )
            ],
        ).model_dump()

    async def school_analytics(
        self,
        *,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        self._ensure_staff_role(auth)
        await self._get_academic_year_or_404(academic_year_id, auth)
        student_ids = set(
            await self.repo.list_school_student_ids(school_id=auth.school_id)
        )
        progress_items = await self.repo.list_progress(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
            student_ids=student_ids,
            include_milestone=True,
        )
        passports = await self.repo.list_passports(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
            student_ids=student_ids,
        )
        dimensions = await self.repo.list_dimensions(is_active=True)
        milestones = await self.repo.list_milestones(
            is_active=True, include_dimension=True
        )

        active_milestone_count = len(milestones)
        student_count = len(student_ids)
        progress_record_count = len(progress_items)
        unlocked_record_count = sum(
            1
            for item in progress_items
            if item.status == SkillProgressStatus.UNLOCKED.value
        )
        possible_records = student_count * active_milestone_count
        average_overall_score = round(
            (unlocked_record_count / possible_records) * 100.0
            if possible_records
            else 0.0,
            2,
        )

        return SkillSchoolAnalyticsResponse(
            school_id=str(auth.school_id),
            academic_year_id=str(academic_year_id),
            student_count=student_count,
            passport_count=len(passports),
            active_milestone_count=active_milestone_count,
            progress_record_count=progress_record_count,
            unlocked_record_count=unlocked_record_count,
            average_overall_score=average_overall_score,
            dimension_summaries=[
                SkillDimensionAnalyticsResponse.model_validate(item)
                for item in self._build_dimension_summaries(
                    dimensions=dimensions,
                    milestones=milestones,
                    progress_items=progress_items,
                )
            ],
        ).model_dump()

    async def leaderboard(
        self,
        *,
        class_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        auth: AuthContext,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        self._ensure_staff_role(auth)
        await self._get_class_or_404(class_id, auth)
        await self._get_academic_year_or_404(academic_year_id, auth)

        student_ids = set(
            await self.repo.list_class_student_ids(
                class_id=class_id, school_id=auth.school_id
            )
        )
        milestones = await self.repo.list_milestones(
            is_active=True, include_dimension=False
        )
        total_milestones = len(milestones)
        progress_items = await self.repo.list_progress(
            school_id=auth.school_id,
            academic_year_id=academic_year_id,
            student_ids=student_ids,
            include_milestone=False,
        )

        grouped: dict[uuid.UUID, dict[str, float]] = {
            student_id: {"unlocked": 0, "total": float(total_milestones)}
            for student_id in student_ids
        }
        for item in progress_items:
            bucket = grouped.setdefault(
                item.student_id, {"unlocked": 0, "total": float(total_milestones)}
            )
            if item.status == SkillProgressStatus.UNLOCKED.value:
                bucket["unlocked"] += 1

        ranked_rows = []
        for student_id, values in grouped.items():
            total = int(values["total"])
            unlocked = int(values["unlocked"])
            overall_score = round((unlocked / total) * 100.0 if total else 0.0, 2)
            ranked_rows.append((student_id, total, unlocked, overall_score))
        ranked_rows.sort(key=lambda row: (-row[3], -row[2], str(row[0])))

        results = []
        for rank, (student_id, total, unlocked, overall_score) in enumerate(
            ranked_rows[: max(limit, 0)],
            start=1,
        ):
            results.append(
                SkillLeaderboardEntryResponse(
                    rank=rank,
                    student_id=str(student_id),
                    alias=f"Student {rank}",
                    total_milestones=total,
                    unlocked_milestones=unlocked,
                    overall_score=overall_score,
                ).model_dump()
            )
        return results


class SkillDimensionService(SkillPassportService):
    """Facade for dimension-oriented operations."""


class SkillMilestoneService(SkillPassportService):
    """Facade for milestone-oriented operations."""


class SkillProgressService(SkillPassportService):
    """Facade for progress-oriented operations."""


class SkillAnalyticsService(SkillPassportService):
    """Facade for analytics-oriented operations."""


__all__ = [
    "SkillPassportService",
    "SkillDimensionService",
    "SkillMilestoneService",
    "SkillProgressService",
    "SkillAnalyticsService",
]
