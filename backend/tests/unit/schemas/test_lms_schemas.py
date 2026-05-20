"""Unit tests for LMS Pydantic schemas.

Validates content, course, assignment, quiz, and progress schemas.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.schemas.lms import (
    ContentItemResponse,
    CourseResponse,
    AssignmentResponse,
    SubmissionCreateRequest,
    SubmissionResponse,
)
from app.schemas.academic.programs import (
    ProgramCreateRequest,
    ProgramResponse,
    ProgramVersionResponse,
)


# ---------------------------------------------------------------------------
# Content item schemas
# ---------------------------------------------------------------------------
class TestContentItemSchemas:
    """Tests for content item request/response schemas."""

    def test_content_item_response(self) -> None:
        item = ContentItemResponse(
            id="content-1",
            school_id="sch-1",
            title="Math Basics",
            content_type="video",
            subject="mathematics",
            level_band="CP",
            status="published",
        )
        assert item.content_type == "video"


# ---------------------------------------------------------------------------
# Course schemas
# ---------------------------------------------------------------------------
class TestCourseSchemas:
    """Tests for course response schema."""

    def test_course_response(self) -> None:
        course = CourseResponse(
            id="course-1",
            school_id="sch-1",
            class_id=str(uuid.uuid4()),
            title="Mathematics CP",
            description="Basic math for CP",
            teacher_id=str(uuid.uuid4()),
            status="published",
        )
        assert course.status == "published"


# ---------------------------------------------------------------------------
# Assignment schemas
# ---------------------------------------------------------------------------
class TestAssignmentSchemas:
    """Tests for assignment and submission schemas."""

    def test_assignment_response(self) -> None:
        assignment = AssignmentResponse(
            id="assign-1",
            course_id="course-1",
            teacher_id="teacher-1",
            title="Homework 1",
            description="Solve exercises 1-10",
            due_at=datetime.utcnow().isoformat(),
            total_points=20,
        )
        assert assignment.total_points == 20

    def test_submission_create_request(self) -> None:
        assignment_id = uuid.uuid4()
        req = SubmissionCreateRequest(
            assignment_id=assignment_id,
        )
        assert req.assignment_id == assignment_id

    def test_submission_response(self) -> None:
        resp = SubmissionResponse(
            id="sub-1",
            assignment_id="assign-1",
            student_id="stu-1",
            status="submitted",
            submitted_at=datetime.utcnow().isoformat(),
        )
        assert resp.status == "submitted"


# ---------------------------------------------------------------------------
# Program schemas
# ---------------------------------------------------------------------------
class TestProgramSchemas:
    """Tests for program creation and response schemas."""

    def test_program_create_request(self) -> None:
        req = ProgramCreateRequest(
            code="BILINGUAL",
            name="Bilingual Program",
            description="English-French bilingual track",
            level="CP",
        )
        assert req.code == "BILINGUAL"

    def test_program_response(self) -> None:
        resp = ProgramResponse(
            id="prog-1",
            school_id="sch-1",
            code="BILINGUAL",
            name="Bilingual Program",
            level="CP",
            description="English-French bilingual track",
            is_active=True,
            version_label="1.0",
            effective_from=date.today(),
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        assert resp.is_active is True

    def test_program_version_response(self) -> None:
        ver = ProgramVersionResponse(
            id="ver-1",
            school_id="sch-1",
            program_id="prog-1",
            version_label="1.0",
            description=None,
            effective_from=date.today(),
            retired_at=None,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=None,
        )
        assert ver.version_label == "1.0"


# ---------------------------------------------------------------------------
# Edge cases — invalid data
# ---------------------------------------------------------------------------
class TestSchemaEdgeCases:
    """Boundary and error-path tests for LMS schemas."""

    def test_missing_program_code(self) -> None:
        """Programs require a stable code."""
        with pytest.raises(ValidationError):
            ProgramCreateRequest(
                name="Empty Program",
            )

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            SubmissionCreateRequest()
