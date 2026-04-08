"""Repository helpers for LMS courses, assignments, submissions, content, and assessments."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import exists, func, select

from app.core.filtering import FilterSpec, SortSpec, apply_filters, apply_sort
from app.core.response import decode_cursor
from app.core.search import apply_search
from app.models.erp import Class, Enrollment
from app.models.iam import ParentChildLink, User
from app.models.lms import (
    Activity,
    ActivitySession,
    Assessment,
    AssessmentResult,
    Assignment,
    ClassContentAssignment,
    ContentItem,
    ContentItemAsset,
    ContentProgress,
    ContentSubmission,
    Course,
    Grade,
    Submission,
    SubmissionFile,
)
from app.repositories.base import BaseRepository


class LMSRepository(BaseRepository):
    """Data access helpers for LMS workflows."""

    async def _paginate_scalars(
        self,
        query,
        *,
        limit: int,
    ) -> tuple[list[Any], bool]:
        result = await self.db.execute(query.limit(limit + 1))
        items = list(result.scalars().all())
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        return items, has_more

    async def _paginate_rows(
        self,
        query,
        *,
        limit: int,
    ) -> tuple[list[Any], bool]:
        result = await self.db.execute(query.limit(limit + 1))
        rows = list(result.all())
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]
        return rows, has_more

    async def get_user(
        self,
        user_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def list_activities(
        self,
        *,
        school_id: uuid.UUID,
        activity_type: str | None,
        difficulty: str | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Activity], bool]:
        query = select(Activity).where(
            (Activity.school_id == school_id) | (Activity.school_id.is_(None))
        )

        if activity_type:
            query = query.where(Activity.type == activity_type)
        if difficulty:
            query = query.where(Activity.difficulty == difficulty)

        query = apply_filters(query, Activity, filters)
        if search:
            query = apply_search(query, Activity, search)
        query = apply_sort(query, Activity, sort, default_column=Activity.id)

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(Activity.id > last_id)

        return await self._paginate_scalars(query, limit=limit)

    async def get_activity(
        self,
        activity_id: uuid.UUID,
    ) -> Activity | None:
        result = await self.db.execute(
            select(Activity).where(Activity.id == activity_id)
        )
        return result.scalar_one_or_none()

    async def get_next_activity_attempt_no(
        self,
        *,
        student_id: uuid.UUID,
        activity_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.coalesce(func.max(ActivitySession.attempt_no), 0)).where(
                ActivitySession.student_id == student_id,
                ActivitySession.activity_id == activity_id,
            )
        )
        return int(result.scalar() or 0) + 1

    async def create_activity_session(
        self,
        **kwargs: Any,
    ) -> ActivitySession:
        session = ActivitySession(**kwargs)
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_activity_session(
        self,
        session_id: uuid.UUID,
    ) -> ActivitySession | None:
        result = await self.db.execute(
            select(ActivitySession).where(ActivitySession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def save_activity_session(
        self,
        session: ActivitySession,
    ) -> ActivitySession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_class(
        self,
        class_id: uuid.UUID,
    ) -> Class | None:
        result = await self.db.execute(select(Class).where(Class.id == class_id))
        return result.scalar_one_or_none()

    async def list_teacher_class_ids(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        from app.models.erp import TeacherAssignment

        result = await self.db.execute(
            select(TeacherAssignment.class_id).where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.school_id == school_id,
            )
        )
        return set(result.scalars().all())

    async def list_parent_child_ids(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(ParentChildLink.child_user_id).where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_student_class_ids(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(Enrollment.class_id).where(
                Enrollment.student_id == student_id,
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
        )
        return set(result.scalars().all())

    async def student_is_enrolled_in_class(
        self,
        *,
        student_id: uuid.UUID,
        class_id: uuid.UUID,
    ) -> bool:
        result = await self.db.execute(
            select(
                exists().where(
                    Enrollment.student_id == student_id,
                    Enrollment.class_id == class_id,
                    Enrollment.status == "active",
                )
            )
        )
        return bool(result.scalar())

    async def get_course(
        self,
        course_id: uuid.UUID,
    ) -> Course | None:
        result = await self.db.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()

    async def create_course(
        self,
        **kwargs: Any,
    ) -> Course:
        course = Course(**kwargs)
        self.db.add(course)
        await self.db.flush()
        return course

    async def list_courses(
        self,
        *,
        school_id: uuid.UUID,
        class_id: uuid.UUID | None,
        teacher_class_ids: set[uuid.UUID] | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Course], bool]:
        query = select(Course).where(Course.school_id == school_id)

        if class_id is not None:
            query = query.where(Course.class_id == class_id)

        if teacher_class_ids is not None:
            if not teacher_class_ids:
                return [], False
            query = query.where(Course.class_id.in_(teacher_class_ids))

        query = apply_filters(query, Course, filters)
        if search:
            query = apply_search(query, Course, search)
        query = apply_sort(query, Course, sort, default_column=Course.id)

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(Course.id > last_id)

        return await self._paginate_scalars(query, limit=limit)

    async def get_assignment(
        self,
        assignment_id: uuid.UUID,
    ) -> Assignment | None:
        result = await self.db.execute(
            select(Assignment).where(Assignment.id == assignment_id)
        )
        return result.scalar_one_or_none()

    async def get_assignment_with_course(
        self,
        assignment_id: uuid.UUID,
    ) -> tuple[Assignment, Course] | None:
        result = await self.db.execute(
            select(Assignment, Course)
            .join(Course, Course.id == Assignment.course_id)
            .where(Assignment.id == assignment_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        assignment, course = row
        return assignment, course

    async def create_assignment(
        self,
        **kwargs: Any,
    ) -> Assignment:
        assignment = Assignment(**kwargs)
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def save_assignment(
        self,
        assignment: Assignment,
    ) -> Assignment:
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def list_assignments(
        self,
        *,
        school_id: uuid.UUID,
        course_id: uuid.UUID | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Assignment], bool]:
        query = select(Assignment)

        if course_id is not None:
            query = query.where(Assignment.course_id == course_id)
        else:
            query = query.join(Course).where(Course.school_id == school_id)

        query = apply_filters(query, Assignment, filters)
        if search:
            query = apply_search(query, Assignment, search)
        query = apply_sort(query, Assignment, sort, default_column=Assignment.id)

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(Assignment.id > last_id)

        return await self._paginate_scalars(query, limit=limit)

    async def get_submission(
        self,
        submission_id: uuid.UUID,
    ) -> Submission | None:
        result = await self.db.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        return result.scalar_one_or_none()

    async def get_submission_with_context(
        self,
        submission_id: uuid.UUID,
    ) -> tuple[Submission, Assignment, Course] | None:
        result = await self.db.execute(
            select(Submission, Assignment, Course)
            .join(Assignment, Assignment.id == Submission.assignment_id)
            .join(Course, Course.id == Assignment.course_id)
            .where(Submission.id == submission_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        submission, assignment, course = row
        return submission, assignment, course

    async def find_active_submission(
        self,
        *,
        assignment_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> Submission | None:
        result = await self.db.execute(
            select(Submission).where(
                Submission.assignment_id == assignment_id,
                Submission.student_id == student_id,
                Submission.status.in_(["draft", "submitted"]),
            )
        )
        return result.scalar_one_or_none()

    async def create_submission(
        self,
        **kwargs: Any,
    ) -> Submission:
        submission = Submission(**kwargs)
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def save_submission(
        self,
        submission: Submission,
    ) -> Submission:
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def get_grade_for_submission(
        self,
        submission_id: uuid.UUID,
    ) -> Grade | None:
        result = await self.db.execute(
            select(Grade).where(Grade.submission_id == submission_id)
        )
        return result.scalar_one_or_none()

    async def create_grade(
        self,
        **kwargs: Any,
    ) -> Grade:
        grade = Grade(**kwargs)
        self.db.add(grade)
        await self.db.flush()
        return grade

    async def save_grade(
        self,
        grade: Grade,
    ) -> Grade:
        self.db.add(grade)
        await self.db.flush()
        return grade

    async def count_submission_files(
        self,
        submission_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count()).where(SubmissionFile.submission_id == submission_id)
        )
        return int(result.scalar() or 0)

    async def create_submission_file(
        self,
        **kwargs: Any,
    ) -> SubmissionFile:
        submission_file = SubmissionFile(**kwargs)
        self.db.add(submission_file)
        await self.db.flush()
        return submission_file

    async def get_submission_file(
        self,
        *,
        submission_id: uuid.UUID,
        file_id: uuid.UUID,
    ) -> SubmissionFile | None:
        result = await self.db.execute(
            select(SubmissionFile).where(
                SubmissionFile.id == file_id,
                SubmissionFile.submission_id == submission_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_submission_files(
        self,
        submission_id: uuid.UUID,
    ) -> list[SubmissionFile]:
        result = await self.db.execute(
            select(SubmissionFile).where(SubmissionFile.submission_id == submission_id)
        )
        return list(result.scalars().all())

    async def get_content_item(
        self,
        content_item_id: uuid.UUID,
    ) -> ContentItem | None:
        result = await self.db.execute(
            select(ContentItem).where(ContentItem.id == content_item_id)
        )
        return result.scalar_one_or_none()

    async def list_content_items(
        self,
        *,
        school_id: uuid.UUID,
        content_type: str | None,
        level_band: str | None,
        language: str | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[ContentItem], bool]:
        query = select(ContentItem).where(
            ContentItem.status == "published",
            (ContentItem.school_id == school_id) | (ContentItem.school_id.is_(None)),
        )

        if content_type:
            query = query.where(ContentItem.content_type == content_type)
        if level_band:
            query = query.where(ContentItem.level_band == level_band)
        if language:
            query = query.where(ContentItem.language == language)

        query = apply_filters(query, ContentItem, filters)
        if search:
            query = apply_search(query, ContentItem, search)
        query = apply_sort(query, ContentItem, sort, default_column=ContentItem.id)

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(ContentItem.id > last_id)

        return await self._paginate_scalars(query, limit=limit)

    async def get_content_progress(
        self,
        *,
        student_id: uuid.UUID,
        content_item_id: uuid.UUID,
    ) -> ContentProgress | None:
        result = await self.db.execute(
            select(ContentProgress).where(
                ContentProgress.student_id == student_id,
                ContentProgress.content_item_id == content_item_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_content_progress(
        self,
        **kwargs: Any,
    ) -> ContentProgress:
        progress = ContentProgress(**kwargs)
        self.db.add(progress)
        await self.db.flush()
        return progress

    async def save_content_progress(
        self,
        progress: ContentProgress,
    ) -> ContentProgress:
        self.db.add(progress)
        await self.db.flush()
        return progress

    async def get_content_asset(
        self,
        *,
        content_item_id: uuid.UUID,
        asset_id: uuid.UUID,
    ) -> ContentItemAsset | None:
        result = await self.db.execute(
            select(ContentItemAsset).where(
                ContentItemAsset.id == asset_id,
                ContentItemAsset.content_item_id == content_item_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_content_asset(
        self,
        **kwargs: Any,
    ) -> ContentItemAsset:
        asset = ContentItemAsset(**kwargs)
        self.db.add(asset)
        await self.db.flush()
        return asset

    async def delete_content_asset(
        self,
        asset: ContentItemAsset,
    ) -> None:
        await self.db.delete(asset)
        await self.db.flush()

    async def browse_content_library(
        self,
        *,
        school_id: uuid.UUID,
        content_type: str | None,
        level_band: str | None,
        subject: str | None,
        language: str | None,
        origin: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[ContentItem], bool]:
        query = select(ContentItem).where(
            ContentItem.status == "published",
            (ContentItem.school_id == school_id) | (ContentItem.school_id.is_(None)),
        )

        if content_type:
            query = query.where(ContentItem.content_type == content_type)
        if level_band:
            query = query.where(ContentItem.level_band == level_band)
        if subject:
            query = query.where(ContentItem.subject == subject)
        if language:
            query = query.where(ContentItem.language == language)
        if origin:
            query = query.where(ContentItem.origin == origin)

        query = query.order_by(ContentItem.id)

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(ContentItem.id > last_id)

        return await self._paginate_scalars(query, limit=limit)

    async def find_class_content_assignment(
        self,
        *,
        class_id: uuid.UUID,
        content_item_id: uuid.UUID,
    ) -> ClassContentAssignment | None:
        result = await self.db.execute(
            select(ClassContentAssignment).where(
                ClassContentAssignment.class_id == class_id,
                ClassContentAssignment.content_item_id == content_item_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_class_content_assignment(
        self,
        **kwargs: Any,
    ) -> ClassContentAssignment:
        assignment = ClassContentAssignment(**kwargs)
        self.db.add(assignment)
        await self.db.flush()
        return assignment

    async def get_class_content_assignment(
        self,
        assignment_id: uuid.UUID,
    ) -> ClassContentAssignment | None:
        result = await self.db.execute(
            select(ClassContentAssignment).where(
                ClassContentAssignment.id == assignment_id
            )
        )
        return result.scalar_one_or_none()

    async def delete_class_content_assignment(
        self,
        assignment: ClassContentAssignment,
    ) -> None:
        await self.db.delete(assignment)
        await self.db.flush()

    async def find_active_content_submission(
        self,
        *,
        content_item_id: uuid.UUID,
        submitted_by: uuid.UUID,
    ) -> ContentSubmission | None:
        result = await self.db.execute(
            select(ContentSubmission).where(
                ContentSubmission.content_item_id == content_item_id,
                ContentSubmission.submitted_by == submitted_by,
                ContentSubmission.status.in_(["PENDING", "UNDER_REVIEW"]),
            )
        )
        return result.scalar_one_or_none()

    async def create_content_submission(
        self,
        **kwargs: Any,
    ) -> ContentSubmission:
        submission = ContentSubmission(**kwargs)
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def list_my_content_submissions(
        self,
        *,
        submitted_by: uuid.UUID,
        status: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[tuple[ContentSubmission, ContentItem]], bool]:
        query = (
            select(ContentSubmission, ContentItem)
            .join(ContentItem, ContentSubmission.content_item_id == ContentItem.id)
            .where(ContentSubmission.submitted_by == submitted_by)
            .order_by(ContentSubmission.id)
        )

        if status:
            query = query.where(ContentSubmission.status == status)

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(ContentSubmission.id > last_id)

        return await self._paginate_rows(query, limit=limit)

    async def list_class_content(
        self,
        *,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[tuple[ClassContentAssignment, ContentItem]], bool]:
        query = (
            select(ClassContentAssignment, ContentItem)
            .join(ContentItem, ClassContentAssignment.content_item_id == ContentItem.id)
            .where(
                ClassContentAssignment.class_id == class_id,
                ClassContentAssignment.school_id == school_id,
                ContentItem.status == "published",
            )
            .order_by(ClassContentAssignment.id)
        )

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(ClassContentAssignment.id > last_id)

        return await self._paginate_rows(query, limit=limit)

    async def create_assessment(
        self,
        **kwargs: Any,
    ) -> Assessment:
        assessment = Assessment(**kwargs)
        self.db.add(assessment)
        await self.db.flush()
        return assessment

    async def get_assessment(
        self,
        assessment_id: uuid.UUID,
    ) -> Assessment | None:
        result = await self.db.execute(
            select(Assessment).where(Assessment.id == assessment_id)
        )
        return result.scalar_one_or_none()

    async def get_assessment_with_class(
        self,
        assessment_id: uuid.UUID,
    ) -> tuple[Assessment, Class] | None:
        result = await self.db.execute(
            select(Assessment, Class)
            .join(Class, Class.id == Assessment.class_id)
            .where(Assessment.id == assessment_id)
        )
        row = result.one_or_none()
        if row is None:
            return None
        assessment, class_room = row
        return assessment, class_room

    async def list_assessments(
        self,
        *,
        school_id: uuid.UUID,
        class_id: uuid.UUID | None,
        status: str | None,
        teacher_class_ids: set[uuid.UUID] | None,
        filters: FilterSpec,
        sort: SortSpec,
        search: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Assessment], bool]:
        query = select(Assessment).join(Class).where(Class.school_id == school_id)

        if class_id is not None:
            query = query.where(Assessment.class_id == class_id)
        if status:
            query = query.where(Assessment.status == status)
        if teacher_class_ids is not None:
            if not teacher_class_ids:
                return [], False
            query = query.where(Assessment.class_id.in_(teacher_class_ids))

        query = apply_filters(query, Assessment, filters)
        if search:
            query = apply_search(query, Assessment, search)
        query = apply_sort(query, Assessment, sort, default_column=Assessment.id)

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(Assessment.id > last_id)

        return await self._paginate_scalars(query, limit=limit)

    async def save_assessment(
        self,
        assessment: Assessment,
    ) -> Assessment:
        self.db.add(assessment)
        await self.db.flush()
        return assessment

    async def get_assessment_result(
        self,
        *,
        assessment_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> AssessmentResult | None:
        result = await self.db.execute(
            select(AssessmentResult).where(
                AssessmentResult.assessment_id == assessment_id,
                AssessmentResult.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_assessment_result(
        self,
        **kwargs: Any,
    ) -> AssessmentResult:
        result_obj = AssessmentResult(**kwargs)
        self.db.add(result_obj)
        await self.db.flush()
        return result_obj

    async def list_results(
        self,
        *,
        school_id: uuid.UUID,
        student_ids: set[uuid.UUID] | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[tuple[Assignment, Submission, Grade, Course]], bool]:
        query = (
            select(Assignment, Submission, Grade, Course)
            .join(Submission, Submission.assignment_id == Assignment.id)
            .join(Grade, Grade.submission_id == Submission.id)
            .join(Course, Course.id == Assignment.course_id)
            .where(
                Course.school_id == school_id,
                Grade.published_at.is_not(None),
            )
            .order_by(Assignment.id)
        )

        if student_ids is not None:
            if not student_ids:
                return [], False
            query = query.where(Submission.student_id.in_(student_ids))

        if cursor:
            last_id, _ = decode_cursor(cursor)
            query = query.where(Assignment.id > last_id)

        return await self._paginate_rows(query, limit=limit)


class AssignmentRepository(LMSRepository):
    """Evaluatable-compatible repository view over assignments."""

    async def list_for_class(
        self,
        school_id: uuid.UUID,
        class_id: uuid.UUID,
        *,
        status: str | None = None,
    ) -> list[dict]:
        if status not in {None, "assigned"}:
            return []

        result = await self.db.execute(
            select(Assignment)
            .join(Course, Course.id == Assignment.course_id)
            .where(
                Course.school_id == school_id,
                Course.class_id == class_id,
                Assignment.quiz_id.is_(None),
            )
            .order_by(Assignment.due_at.asc(), Assignment.id.asc())
        )
        assignments = list(result.scalars().all())
        return [
            self._serialize_assignment(assignment=assignment)
            for assignment in assignments
        ]

    async def list_for_student(
        self,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> list[dict]:
        class_ids = await self.list_student_class_ids(
            student_id=student_id,
            school_id=school_id,
        )
        if not class_ids:
            return []

        result = await self.db.execute(
            select(Assignment)
            .join(Course, Course.id == Assignment.course_id)
            .where(
                Course.school_id == school_id,
                Course.class_id.in_(class_ids),
                Assignment.quiz_id.is_(None),
            )
            .order_by(Assignment.due_at.asc(), Assignment.id.asc())
        )
        assignments = list(result.scalars().all())

        items: list[dict] = []
        for assignment in assignments:
            submission = await self._get_latest_submission_for_student(
                assignment_id=assignment.id,
                student_id=student_id,
            )
            items.append(
                self._serialize_assignment(
                    assignment=assignment,
                    status=submission.status if submission is not None else "assigned",
                )
            )
        return items

    async def get_detail(self, item_id: uuid.UUID) -> dict | None:
        bundle = await self.get_assignment_with_course(item_id)
        if bundle is None:
            return None
        assignment, course = bundle
        return {
            **self._serialize_assignment(assignment=assignment),
            "course_id": str(course.id),
            "class_id": str(course.class_id),
            "teacher_id": str(assignment.teacher_id),
            "description": assignment.description,
            "exercise_type": assignment.exercise_type,
            "exercise_pdf_path": assignment.exercise_pdf_path,
        }

    async def get_results(self, item_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(Submission, Grade)
            .outerjoin(Grade, Grade.submission_id == Submission.id)
            .where(Submission.assignment_id == item_id)
            .order_by(Submission.created_at.desc())
        )
        rows = list(result.all())
        return [
            {
                "student_id": str(submission.student_id),
                "submission_id": str(submission.id),
                "status": submission.status,
                "submitted_at": _dt_to_iso(submission.submitted_at),
                "score": float(grade.score) if grade is not None else None,
                "feedback_text": grade.feedback_text if grade is not None else None,
                "published_at": _dt_to_iso(grade.published_at)
                if grade is not None
                else None,
            }
            for submission, grade in rows
        ]

    async def _get_latest_submission_for_student(
        self,
        *,
        assignment_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> Submission | None:
        result = await self.db.execute(
            select(Submission)
            .where(
                Submission.assignment_id == assignment_id,
                Submission.student_id == student_id,
            )
            .order_by(Submission.created_at.desc())
        )
        return result.scalars().first()

    def _serialize_assignment(
        self,
        *,
        assignment: Assignment,
        status: str = "assigned",
    ) -> dict:
        return {
            "id": str(assignment.id),
            "title": assignment.title,
            "type": "assignment",
            "due_at": _dt_to_iso(assignment.due_at),
            "status": status,
            "total_points": int(assignment.total_points or 0),
        }


class AssessmentRepository(LMSRepository):
    """Evaluatable-compatible repository view over assessments."""

    async def list_for_class(
        self,
        school_id: uuid.UUID,
        class_id: uuid.UUID,
        *,
        status: str | None = None,
    ) -> list[dict]:
        result = await self.db.execute(
            select(Assessment)
            .join(Class, Class.id == Assessment.class_id)
            .where(
                Class.school_id == school_id,
                Assessment.class_id == class_id,
            )
            .order_by(Assessment.due_at.asc(), Assessment.id.asc())
        )
        assessments = list(result.scalars().all())
        if status is not None:
            assessments = [
                assessment for assessment in assessments if assessment.status == status
            ]
        return [
            self._serialize_assessment(assessment=assessment)
            for assessment in assessments
        ]

    async def list_for_student(
        self,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> list[dict]:
        class_ids = await self.list_student_class_ids(
            student_id=student_id,
            school_id=school_id,
        )
        if not class_ids:
            return []

        result = await self.db.execute(
            select(Assessment)
            .join(Class, Class.id == Assessment.class_id)
            .where(
                Class.school_id == school_id,
                Assessment.class_id.in_(class_ids),
            )
            .order_by(Assessment.due_at.asc(), Assessment.id.asc())
        )
        assessments = list(result.scalars().all())
        items: list[dict] = []
        for assessment in assessments:
            assessment_result = await self.get_assessment_result(
                assessment_id=assessment.id,
                student_id=student_id,
            )
            items.append(
                self._serialize_assessment(
                    assessment=assessment,
                    status=(
                        assessment_result.status
                        if assessment_result is not None
                        else assessment.status
                    ),
                )
            )
        return items

    async def get_detail(self, item_id: uuid.UUID) -> dict | None:
        bundle = await self.get_assessment_with_class(item_id)
        if bundle is None:
            return None
        assessment, class_room = bundle
        return {
            **self._serialize_assessment(assessment=assessment),
            "class_id": str(class_room.id),
            "teacher_id": str(assessment.teacher_id),
            "window_end": _dt_to_iso(assessment.window_end),
        }

    async def get_results(self, item_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(AssessmentResult)
            .where(AssessmentResult.assessment_id == item_id)
            .order_by(AssessmentResult.created_at.desc())
        )
        rows = list(result.scalars().all())
        return [
            {
                "student_id": str(row.student_id),
                "status": row.status,
                "score": float(row.score) if row.score is not None else None,
                "created_at": _dt_to_iso(row.created_at),
            }
            for row in rows
        ]

    def _serialize_assessment(
        self,
        *,
        assessment: Assessment,
        status: str | None = None,
    ) -> dict:
        return {
            "id": str(assessment.id),
            "title": assessment.title,
            "type": "assessment",
            "due_at": _dt_to_iso(assessment.due_at),
            "status": status or assessment.status,
            "total_points": int(assessment.total_points or 0),
        }


def _dt_to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None
