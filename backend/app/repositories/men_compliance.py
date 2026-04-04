"""Repository helpers for MEN compliance workflows."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.erp import AcademicYear
from app.models.iam import User
from app.models.lms import ContentItem, Course
from app.models.men_compliance import (
    ComplianceReport,
    CurriculumMapping,
    MenCurriculum,
    MenObjective,
)
from app.repositories.base import BaseRepository


class ComplianceRepository(BaseRepository):
    """Data access for curricula, objectives, mappings, and compliance reports."""

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_academic_year(self, academic_year_id: uuid.UUID) -> AcademicYear | None:
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.id == academic_year_id)
        )
        return result.scalar_one_or_none()

    async def get_course(self, course_id: uuid.UUID) -> Course | None:
        result = await self.db.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()

    async def get_content_item(self, content_item_id: uuid.UUID) -> ContentItem | None:
        result = await self.db.execute(
            select(ContentItem).where(ContentItem.id == content_item_id)
        )
        return result.scalar_one_or_none()

    async def get_curriculum(
        self,
        curriculum_id: uuid.UUID,
        *,
        include_objectives: bool = False,
    ) -> MenCurriculum | None:
        query = select(MenCurriculum).where(MenCurriculum.id == curriculum_id)
        if include_objectives:
            query = query.options(selectinload(MenCurriculum.objectives))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_curriculum_by_scope(
        self,
        *,
        level: str,
        grade: str,
        subject: str,
        academic_year: str,
        version: str,
    ) -> MenCurriculum | None:
        result = await self.db.execute(
            select(MenCurriculum).where(
                MenCurriculum.level == level,
                MenCurriculum.grade == grade,
                MenCurriculum.subject == subject,
                MenCurriculum.academic_year == academic_year,
                MenCurriculum.version == version,
            )
        )
        return result.scalar_one_or_none()

    async def list_curricula(
        self,
        *,
        level: str | None = None,
        grade: str | None = None,
        subject: str | None = None,
        academic_year: str | None = None,
        is_active: bool | None = None,
    ) -> list[MenCurriculum]:
        query = select(MenCurriculum)
        if level is not None:
            query = query.where(MenCurriculum.level == level)
        if grade is not None:
            query = query.where(MenCurriculum.grade == grade)
        if subject is not None:
            query = query.where(MenCurriculum.subject == subject)
        if academic_year is not None:
            query = query.where(MenCurriculum.academic_year == academic_year)
        if is_active is not None:
            query = query.where(MenCurriculum.is_active.is_(is_active))
        result = await self.db.execute(
            query.order_by(
                MenCurriculum.level.asc(),
                MenCurriculum.grade.asc(),
                MenCurriculum.subject.asc(),
                MenCurriculum.created_at.asc(),
            )
        )
        return list(result.scalars().all())

    async def create_curriculum(self, curriculum: MenCurriculum) -> MenCurriculum:
        self.db.add(curriculum)
        await self.db.flush()
        return curriculum

    async def save_curriculum(self, curriculum: MenCurriculum) -> MenCurriculum:
        self.db.add(curriculum)
        await self.db.flush()
        return curriculum

    async def get_objective(
        self,
        objective_id: uuid.UUID,
        *,
        include_curriculum: bool = False,
    ) -> MenObjective | None:
        query = select(MenObjective).where(MenObjective.id == objective_id)
        if include_curriculum:
            query = query.options(selectinload(MenObjective.curriculum))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_objective_by_code(
        self,
        *,
        curriculum_id: uuid.UUID,
        code: str,
    ) -> MenObjective | None:
        result = await self.db.execute(
            select(MenObjective).where(
                MenObjective.curriculum_id == curriculum_id,
                MenObjective.code == code,
            )
        )
        return result.scalar_one_or_none()

    async def list_objectives(
        self,
        *,
        curriculum_id: uuid.UUID,
        trimester: int | None = None,
        include_curriculum: bool = False,
    ) -> list[MenObjective]:
        query = select(MenObjective).where(MenObjective.curriculum_id == curriculum_id)
        if trimester is not None:
            query = query.where(MenObjective.trimester == trimester)
        if include_curriculum:
            query = query.options(selectinload(MenObjective.curriculum))
        result = await self.db.execute(
            query.order_by(MenObjective.display_order.asc(), MenObjective.code.asc())
        )
        return list(result.scalars().all())

    async def create_objective(self, objective: MenObjective) -> MenObjective:
        self.db.add(objective)
        await self.db.flush()
        return objective

    async def save_objective(self, objective: MenObjective) -> MenObjective:
        self.db.add(objective)
        await self.db.flush()
        return objective

    async def get_mapping(
        self,
        mapping_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_objective: bool = False,
    ) -> CurriculumMapping | None:
        query = select(CurriculumMapping).where(CurriculumMapping.id == mapping_id)
        if school_id is not None:
            query = query.where(CurriculumMapping.school_id == school_id)
        if include_objective:
            query = query.options(
                selectinload(CurriculumMapping.objective).selectinload(
                    MenObjective.curriculum
                )
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_mapping(
        self,
        *,
        school_id: uuid.UUID,
        objective_id: uuid.UUID,
        course_id: uuid.UUID | None = None,
        content_item_id: uuid.UUID | None = None,
    ) -> CurriculumMapping | None:
        query = select(CurriculumMapping).where(
            CurriculumMapping.school_id == school_id,
            CurriculumMapping.objective_id == objective_id,
        )
        if course_id is not None:
            query = query.where(CurriculumMapping.course_id == course_id)
        else:
            query = query.where(CurriculumMapping.course_id.is_(None))
        if content_item_id is not None:
            query = query.where(CurriculumMapping.content_item_id == content_item_id)
        else:
            query = query.where(CurriculumMapping.content_item_id.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_mappings(
        self,
        *,
        school_id: uuid.UUID,
        curriculum_id: uuid.UUID | None = None,
        objective_id: uuid.UUID | None = None,
        course_id: uuid.UUID | None = None,
        content_item_id: uuid.UUID | None = None,
        include_objective: bool = False,
    ) -> list[CurriculumMapping]:
        query = select(CurriculumMapping).where(CurriculumMapping.school_id == school_id)
        if curriculum_id is not None:
            query = query.join(MenObjective, MenObjective.id == CurriculumMapping.objective_id)
            query = query.where(MenObjective.curriculum_id == curriculum_id)
        if objective_id is not None:
            query = query.where(CurriculumMapping.objective_id == objective_id)
        if course_id is not None:
            query = query.where(CurriculumMapping.course_id == course_id)
        if content_item_id is not None:
            query = query.where(CurriculumMapping.content_item_id == content_item_id)
        if include_objective:
            query = query.options(
                selectinload(CurriculumMapping.objective).selectinload(
                    MenObjective.curriculum
                )
            )
        result = await self.db.execute(
            query.order_by(CurriculumMapping.mapped_at.desc(), CurriculumMapping.id.asc())
        )
        return list(result.scalars().all())

    async def create_mapping(self, mapping: CurriculumMapping) -> CurriculumMapping:
        self.db.add(mapping)
        await self.db.flush()
        return mapping

    async def save_mapping(self, mapping: CurriculumMapping) -> CurriculumMapping:
        self.db.add(mapping)
        await self.db.flush()
        return mapping

    async def delete_mapping(self, mapping: CurriculumMapping) -> None:
        await self.db.delete(mapping)
        await self.db.flush()

    async def get_report(
        self,
        report_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_curriculum: bool = False,
    ) -> ComplianceReport | None:
        query = select(ComplianceReport).where(ComplianceReport.id == report_id)
        if school_id is not None:
            query = query.where(ComplianceReport.school_id == school_id)
        if include_curriculum:
            query = query.options(selectinload(ComplianceReport.curriculum))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_reports(
        self,
        *,
        school_id: uuid.UUID,
        curriculum_id: uuid.UUID | None = None,
        academic_year_id: uuid.UUID | None = None,
    ) -> list[ComplianceReport]:
        query = select(ComplianceReport).where(ComplianceReport.school_id == school_id)
        if curriculum_id is not None:
            query = query.where(ComplianceReport.curriculum_id == curriculum_id)
        if academic_year_id is not None:
            query = query.where(ComplianceReport.academic_year_id == academic_year_id)
        query = query.options(selectinload(ComplianceReport.curriculum))
        result = await self.db.execute(
            query.order_by(
                ComplianceReport.generated_at.desc(),
                ComplianceReport.id.asc(),
            )
        )
        return list(result.scalars().all())

    async def create_report(self, report: ComplianceReport) -> ComplianceReport:
        self.db.add(report)
        await self.db.flush()
        return report

    async def save_report(self, report: ComplianceReport) -> ComplianceReport:
        self.db.add(report)
        await self.db.flush()
        return report


__all__ = ["ComplianceRepository"]
