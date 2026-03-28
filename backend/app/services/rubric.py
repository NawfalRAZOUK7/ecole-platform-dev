"""Rubric service — CRUD and rubric-based grading workflows."""

from __future__ import annotations

import uuid

from app.core.dependencies import (
    AuthContext,
    verify_parent_child_ownership,
    verify_school_boundary,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.unit_of_work import UnitOfWork
from app.domain.value_objects.grade import MoroccanGrade
from app.models.lms import Rubric
from app.repositories.lms import LMSRepository
from app.repositories.rubric import RubricRepository
from app.schemas.rubric import RubricCreateRequest, RubricScoreInput
from app.services.audit import AuditService
from app.services.lms._helpers import LMSServiceBase, calculate_late_penalty, _utc_now


class RubricService(LMSServiceBase):
    """Handles rubric CRUD, duplication, grading, and rubric results."""

    def __init__(self, db) -> None:
        super().__init__(db)
        self.rubric_repo = RubricRepository(db)

    def _level_to_dict(self, level) -> dict:
        return {
            "id": str(level.id),
            "criterion_id": str(level.criterion_id),
            "label": level.label,
            "description": level.description,
            "points": float(level.points),
            "position": level.position,
        }

    def _criterion_to_dict(self, criterion) -> dict:
        return {
            "id": str(criterion.id),
            "rubric_id": str(criterion.rubric_id),
            "title": criterion.title,
            "description": criterion.description,
            "weight": float(criterion.weight),
            "position": criterion.position,
            "levels": [self._level_to_dict(level) for level in criterion.levels],
        }

    def _rubric_to_dict(self, rubric: Rubric) -> dict:
        return {
            "id": str(rubric.id),
            "school_id": str(rubric.school_id),
            "teacher_id": str(rubric.teacher_id),
            "title": rubric.title,
            "description": rubric.description,
            "total_points": rubric.total_points,
            "is_template": rubric.is_template,
            "criteria": [self._criterion_to_dict(item) for item in rubric.criteria],
        }

    def _rubric_score_to_dict(self, rubric_score) -> dict:
        criterion = rubric_score.criterion
        level = rubric_score.level
        return {
            "id": str(rubric_score.id),
            "submission_id": str(rubric_score.submission_id),
            "criterion_id": str(rubric_score.criterion_id),
            "criterion_title": criterion.title if criterion is not None else None,
            "criterion_weight": (
                float(criterion.weight) if criterion is not None else None
            ),
            "level_id": str(rubric_score.level_id) if rubric_score.level_id else None,
            "level_label": level.label if level is not None else None,
            "level_points": float(level.points) if level is not None else None,
            "points_awarded": float(rubric_score.points_awarded),
            "comment": rubric_score.comment,
        }

    def _ensure_can_view_rubric(self, rubric: Rubric, auth: AuthContext) -> None:
        verify_school_boundary(rubric.school_id, auth)
        if auth.role == "TCH" and rubric.teacher_id != auth.user_id and not rubric.is_template:
            raise NotFoundError("Rubric not found", error_code="ERR-LMS-404")

    def _ensure_can_duplicate_rubric(self, rubric: Rubric, auth: AuthContext) -> None:
        verify_school_boundary(rubric.school_id, auth)
        if auth.role == "TCH" and rubric.teacher_id != auth.user_id and not rubric.is_template:
            raise NotFoundError("Rubric not found", error_code="ERR-LMS-404")

    def _rubric_feedback_summary(self, grade: MoroccanGrade) -> str:
        return f"Rubric graded: {grade.mention}. See rubric results for criterion details."

    def _calculate_grade(
        self,
        *,
        rubric: Rubric,
        scores: list[RubricScoreInput],
    ) -> MoroccanGrade:
        if rubric.total_points <= 0:
            raise ValidationError(
                "Rubric total_points must be greater than zero",
                error_code="ERR-LMS-422",
            )
        if not rubric.criteria:
            raise ValidationError(
                "Rubric must have at least one criterion",
                error_code="ERR-LMS-422",
            )

        criteria_by_id = {criterion.id: criterion for criterion in rubric.criteria}
        if len(scores) != len(criteria_by_id):
            raise ValidationError(
                "A score entry is required for every rubric criterion",
                error_code="ERR-LMS-422",
            )

        total_weight = sum(float(criterion.weight) for criterion in rubric.criteria)
        if total_weight <= 0:
            raise ValidationError(
                "Rubric criteria weights must sum to more than zero",
                error_code="ERR-LMS-422",
            )

        seen_ids: set[uuid.UUID] = set()
        weighted_total = 0.0
        for item in scores:
            criterion = criteria_by_id.get(item.criterion_id)
            if criterion is None:
                raise ValidationError(
                    "Rubric score contains a criterion outside the assigned rubric",
                    error_code="ERR-LMS-422",
                )
            if item.criterion_id in seen_ids:
                raise ValidationError(
                    "Each rubric criterion can only be graded once",
                    error_code="ERR-LMS-422",
                )
            seen_ids.add(item.criterion_id)

            if item.level_id is not None:
                level = next(
                    (level for level in criterion.levels if level.id == item.level_id),
                    None,
                )
                if level is None:
                    raise ValidationError(
                        "Rubric level does not belong to the selected criterion",
                        error_code="ERR-LMS-422",
                    )

            if item.points_awarded > rubric.total_points:
                raise ValidationError(
                    "points_awarded cannot exceed rubric.total_points",
                    error_code="ERR-LMS-422",
                )

            normalized_points = float(item.points_awarded) / float(rubric.total_points)
            weighted_total += normalized_points * float(criterion.weight)

        return MoroccanGrade.from_float((weighted_total / total_weight) * 20)

    async def create_rubric(
        self,
        *,
        body: RubricCreateRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        if body.total_points <= 0:
            raise ValidationError(
                "Rubric total_points must be greater than zero",
                error_code="ERR-LMS-422",
            )
        if not body.criteria:
            raise ValidationError(
                "Rubric must include at least one criterion",
                error_code="ERR-LMS-422",
            )
        for criterion in body.criteria:
            if not criterion.levels:
                raise ValidationError(
                    "Every rubric criterion must include at least one level",
                    error_code="ERR-LMS-422",
                )

        async with UnitOfWork(self.db) as uow:
            repo = RubricRepository(uow.session)
            audit = AuditService(uow.session)
            rubric = await repo.create_rubric(
                school_id=auth.school_id,
                teacher_id=auth.user_id,
                title=body.title,
                description=body.description,
                total_points=body.total_points,
                is_template=body.is_template,
            )

            for criterion_index, criterion_input in enumerate(body.criteria):
                criterion = await repo.create_criterion(
                    rubric_id=rubric.id,
                    title=criterion_input.title,
                    description=criterion_input.description,
                    weight=criterion_input.weight,
                    position=criterion_input.position
                    if criterion_input.position >= 0
                    else criterion_index,
                )
                for level_index, level_input in enumerate(criterion_input.levels):
                    await repo.create_level(
                        criterion_id=criterion.id,
                        label=level_input.label,
                        description=level_input.description,
                        points=level_input.points,
                        position=level_input.position
                        if level_input.position >= 0
                        else level_index,
                    )

            rubric = await repo.get_rubric(rubric.id)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="RUBRIC_CREATED",
                outcome="success",
                target_type="rubric",
                target_id=rubric.id,
                entity_after={
                    "title": rubric.title,
                    "criterion_count": len(rubric.criteria),
                    "is_template": rubric.is_template,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return self._rubric_to_dict(rubric)

    async def get_rubric(
        self,
        *,
        rubric_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        rubric = await self.rubric_repo.get_rubric(rubric_id)
        if rubric is None:
            raise NotFoundError("Rubric not found", error_code="ERR-LMS-404")
        self._ensure_can_view_rubric(rubric, auth)
        return self._rubric_to_dict(rubric)

    async def list_rubrics(
        self,
        *,
        auth: AuthContext,
    ) -> list[dict]:
        teacher_id = None if auth.role == "ADM" else auth.user_id
        rubrics = await self.rubric_repo.list_rubrics(
            school_id=auth.school_id,
            teacher_id=teacher_id,
        )
        return [self._rubric_to_dict(rubric) for rubric in rubrics]

    async def duplicate_rubric(
        self,
        *,
        rubric_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        source = await self.rubric_repo.get_rubric(rubric_id)
        if source is None:
            raise NotFoundError("Rubric not found", error_code="ERR-LMS-404")
        self._ensure_can_duplicate_rubric(source, auth)

        async with UnitOfWork(self.db) as uow:
            repo = RubricRepository(uow.session)
            audit = AuditService(uow.session)
            duplicated = await repo.create_rubric(
                school_id=auth.school_id,
                teacher_id=auth.user_id,
                title=f"{source.title} (Copy)",
                description=source.description,
                total_points=source.total_points,
                is_template=False,
            )
            for criterion in source.criteria:
                duplicated_criterion = await repo.create_criterion(
                    rubric_id=duplicated.id,
                    title=criterion.title,
                    description=criterion.description,
                    weight=criterion.weight,
                    position=criterion.position,
                )
                for level in criterion.levels:
                    await repo.create_level(
                        criterion_id=duplicated_criterion.id,
                        label=level.label,
                        description=level.description,
                        points=level.points,
                        position=level.position,
                    )

            duplicated = await repo.get_rubric(duplicated.id)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="RUBRIC_DUPLICATED",
                outcome="success",
                target_type="rubric",
                target_id=duplicated.id,
                entity_after={
                    "source_rubric_id": str(source.id),
                    "title": duplicated.title,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        return self._rubric_to_dict(duplicated)

    async def grade_with_rubric(
        self,
        *,
        submission_id: uuid.UUID,
        scores: list[RubricScoreInput],
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        bundle = await self.rubric_repo.get_submission_with_rubric_context(submission_id)
        if bundle is None:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        submission, assignment, course, rubric = bundle
        verify_school_boundary(course.school_id, auth)

        if auth.role == "TCH" and course.teacher_id != auth.user_id:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        if submission.status not in ("submitted", "graded"):
            raise ValidationError(
                "Submission must be in submitted or graded status to be graded",
                error_code="ERR-LMS-422",
            )
        if rubric is None or assignment.rubric_id is None:
            raise ValidationError(
                "Assignment does not have a rubric attached",
                error_code="ERR-LMS-422",
            )

        rubric = await self.rubric_repo.get_rubric(rubric.id)
        grade_value = self._calculate_grade(rubric=rubric, scores=scores)
        penalty_data = calculate_late_penalty(
            assignment=assignment,
            submission=submission,
            original_score=float(grade_value),
        )
        published_at = _utc_now()
        feedback_text = self._rubric_feedback_summary(grade_value)

        async with UnitOfWork(self.db) as uow:
            rubric_repo = RubricRepository(uow.session)
            lms_repo = LMSRepository(uow.session)
            audit = AuditService(uow.session)
            grade = await lms_repo.get_grade_for_submission(submission_id)

            await rubric_repo.delete_rubric_scores_for_submission(submission_id)
            for item in scores:
                await rubric_repo.create_rubric_score(
                    submission_id=submission_id,
                    criterion_id=item.criterion_id,
                    level_id=item.level_id,
                    points_awarded=item.points_awarded,
                    comment=item.comment,
                )

            if grade is not None:
                grade.score = penalty_data["adjusted_score"]
                grade.original_score = penalty_data["original_score"]
                grade.late_penalty = penalty_data["late_penalty"]
                grade.late_days = penalty_data["late_days"]
                grade.penalty_overridden = False
                grade.feedback_text = feedback_text
                grade.published_at = published_at
                await lms_repo.save_grade(grade)
            else:
                grade = await lms_repo.create_grade(
                    submission_id=submission_id,
                    teacher_id=auth.user_id,
                    score=penalty_data["adjusted_score"],
                    original_score=penalty_data["original_score"],
                    late_penalty=penalty_data["late_penalty"],
                    late_days=penalty_data["late_days"],
                    penalty_overridden=False,
                    feedback_text=feedback_text,
                    published_at=published_at,
                )

            submission.status = "graded"
            await lms_repo.save_submission(submission)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="RUBRIC_GRADED",
                outcome="success",
                target_type="grade",
                target_id=grade.id,
                entity_after={
                    "submission_id": str(submission_id),
                    "rubric_id": str(rubric.id),
                    "score": float(penalty_data["adjusted_score"]),
                    "original_score": float(penalty_data["original_score"]),
                    "late_penalty": float(penalty_data["late_penalty"]),
                    "late_days": int(penalty_data["late_days"]),
                    "mention": grade_value.mention,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        await self._dispatch_grade_published(
            grade=grade,
            submission=submission,
            assignment=assignment,
            course=course,
            actor_id=auth.user_id,
            score=float(penalty_data["adjusted_score"]),
            feedback_text=feedback_text,
        )
        return await self.get_rubric_results(submission_id=submission_id, auth=auth)

    async def get_rubric_results(
        self,
        *,
        submission_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        bundle = await self.rubric_repo.get_submission_with_rubric_context(submission_id)
        if bundle is None:
            raise NotFoundError("Submission not found", error_code="ERR-LMS-404")
        submission, assignment, course, rubric = bundle
        if rubric is None or assignment.rubric_id is None:
            raise NotFoundError("Rubric results not found", error_code="ERR-LMS-404")
        verify_school_boundary(course.school_id, auth)

        if auth.role == "STD":
            if submission.student_id != auth.user_id:
                raise NotFoundError("Rubric results not found", error_code="ERR-LMS-404")
        elif auth.role == "PAR":
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_parent_child_ownership(submission.student_id, child_ids)
        elif auth.role == "TCH" and course.teacher_id != auth.user_id:
            raise NotFoundError("Rubric results not found", error_code="ERR-LMS-404")

        grade = await self.repo.get_grade_for_submission(submission_id)
        if grade is None:
            raise NotFoundError("Rubric results not found", error_code="ERR-LMS-404")
        if grade.published_at is None and auth.role in {"STD", "PAR"}:
            raise NotFoundError("Rubric results not found", error_code="ERR-LMS-404")

        rubric_scores = await self.rubric_repo.list_rubric_scores(submission_id)
        return {
            "submission_id": str(submission.id),
            "assignment_id": str(assignment.id),
            "rubric_id": str(rubric.id),
            "grade_id": str(grade.id),
            "published_at": grade.published_at.isoformat()
            if grade.published_at
            else None,
            "feedback_text": grade.feedback_text,
            "total_score": float(grade.score) if grade.score is not None else None,
            "scores": [self._rubric_score_to_dict(item) for item in rubric_scores],
        }
