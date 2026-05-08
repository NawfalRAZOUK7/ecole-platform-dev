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
from app.schemas.programs import (
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
            title="Math Basics",
            type="video",
            subject="mathematics",
            grade_level="CP",
            url="https://cdn.example.com/video.mp4",
            duration_seconds=300,
        )
        assert item.type == "video"


# ---------------------------------------------------------------------------
# Course schemas
# ---------------------------------------------------------------------------
class TestCourseSchemas:
    """Tests for course response schema."""

    def test_course_response(self) -> None:
        course = CourseResponse(
            id="course-1",
            title="Mathematics CP",
            description="Basic math for CP",
            subject="mathematics",
            grade_level="CP",
            teacher_id=str(uuid.uuid4()),
            content_items=[],
        )
        assert course.grade_level == "CP"


# ---------------------------------------------------------------------------
# Assignment schemas
# ---------------------------------------------------------------------------
class TestAssignmentSchemas:
    """Tests for assignment and submission schemas."""

    def test_assignment_response(self) -> None:
        assignment = AssignmentResponse(
            id="assign-1",
            course_id="course-1",
            title="Homework 1",
            description="Solve exercises 1-10",
            due_date=datetime.utcnow(),
            max_score=20.0,
        )
        assert assignment.max_score == 20.0

    def test_submission_create_request(self) -> None:
        req = SubmissionCreateRequest(
            assignment_id="assign-1",
            content={"answers": ["a", "b", "c"]},
        )
        assert req.assignment_id == "assign-1"

    def test_submission_response(self) -> None:
        resp = SubmissionResponse(
            id="sub-1",
            assignment_id="assign-1",
            student_id="stu-1",
            content={"answers": ["a"]},
            submitted_at=datetime.utcnow(),
            score=None,
            feedback=None,
        )
        assert resp.score is None


# ---------------------------------------------------------------------------
# Program schemas
# ---------------------------------------------------------------------------
class TestProgramSchemas:
    """Tests for program creation and response schemas."""

    def test_program_create_request(self) -> None:
        req = ProgramCreateRequest(
            school_id=uuid.uuid4(),
            name="Bilingual Program",
            description="English-French bilingual track",
            levels=["CP", "CE1", "CE2"],
        )
        assert "CE1" in req.levels

    def test_program_response(self) -> None:
        resp = ProgramResponse(
            id="prog-1",
            school_id="sch-1",
            name="Bilingual Program",
            description="English-French bilingual track",
            levels=["CP", "CE1", "CE2"],
            is_active=True,
            created_at=datetime.utcnow(),
        )
        assert resp.is_active is True

    def test_program_version_response(self) -> None:
        ver = ProgramVersionResponse(
            id="ver-1",
            program_id="prog-1",
            version_number=1,
            effective_date=date.today(),
            rules={},
            created_at=datetime.utcnow(),
        )
        assert ver.version_number == 1


# ---------------------------------------------------------------------------
# Edge cases — invalid data
# ---------------------------------------------------------------------------
class TestSchemaEdgeCases:
    """Boundary and error-path tests for LMS schemas."""

    def test_empty_levels_list(self) -> None:
        """Programs should require at least one level."""
        with pytest.raises(ValidationError):
            ProgramCreateRequest(
                school_id=uuid.uuid4(),
                name="Empty Program",
                levels=[],
            )

    def test_missing_required_fields(self) -> None:
        with pytest.raises(ValidationError):
            SubmissionCreateRequest()
