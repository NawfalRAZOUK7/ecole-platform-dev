"""Unit tests for gradebook service."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import ValidationError
from app.domain.value_objects.grade import MoroccanGrade
from app.schemas.gradebook import GradeCategorySetRequest
from app.services import gradebook as gradebook_module
from app.services.gradebook import GradebookService


def make_auth(role: str = "ADM") -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        self.committed = True


def make_category(name: str, weight: float, position: int):
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=uuid.uuid4(),
        class_id=uuid.uuid4(),
        period_id=uuid.uuid4(),
        name=name,
        weight=weight,
        position=position,
    )


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = GradebookService(AsyncMock())
    service.repo = AsyncMock()
    service.gradebook_repo = AsyncMock()
    service.erp_repo = AsyncMock()

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(gradebook_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        gradebook_module, "GradebookRepository", lambda _session: repo_in_uow
    )
    monkeypatch.setattr(gradebook_module, "AuditService", lambda _session: audit)
    monkeypatch.setattr(
        gradebook_module, "role_has_permission", lambda _role, _perm: True
    )

    return service, repo_in_uow, audit, uow


class TestGradebookHelpers:
    def test_validate_category_weights_rejects_empty_list(self):
        service = GradebookService(AsyncMock())

        with pytest.raises(ValidationError, match="At least one grade category"):
            service._validate_category_weights([])

    def test_validate_category_weights_allows_empty_list_for_read_views(self):
        service = GradebookService(AsyncMock())

        service._validate_category_weights([], allow_empty=True)

    def test_compute_weighted_average_returns_moroccan_grade(self):
        service = GradebookService(AsyncMock())
        categories = [
            make_category("Exams", 0.4, 0),
            make_category("Homework", 0.6, 1),
        ]
        category_averages = {
            categories[0].id: 14.0,
            categories[1].id: 18.0,
        }

        result = service._compute_weighted_average(
            categories=categories,
            category_averages=category_averages,
        )

        assert float(result) == 16.4
        assert result.mention == "Très Bien"


class TestGradebookPublicMethods:
    @pytest.mark.asyncio
    async def test_set_grade_categories_rejects_weights_that_do_not_sum_to_one(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        service._ensure_class_access = AsyncMock(
            return_value=(
                SimpleNamespace(id=uuid.uuid4()),
                SimpleNamespace(id=uuid.uuid4()),
            )
        )

        with pytest.raises(ValidationError, match="weights must sum to 1.0"):
            await service.set_grade_categories(
                body=GradeCategorySetRequest(
                    class_id=uuid.uuid4(),
                    period_id=uuid.uuid4(),
                    categories=[
                        {"name": "Exam", "weight": 0.7, "position": 0},
                        {"name": "Homework", "weight": 0.2, "position": 1},
                    ],
                ),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_compute_student_average_uses_category_rows(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        categories = [
            make_category("Exam", 0.5, 0),
            make_category("Homework", 0.5, 1),
        ]
        service.gradebook_repo.get_student_grades_by_category.return_value = [
            (categories[0], 14.0),
            (categories[1], 18.0),
        ]

        result = await service.compute_student_average(
            student_id=uuid.uuid4(),
            class_id=uuid.uuid4(),
            period_id=uuid.uuid4(),
        )

        assert isinstance(result, MoroccanGrade)
        assert float(result) == 16.0
        assert result.mention == "Très Bien"

    @pytest.mark.asyncio
    async def test_compute_class_averages_persists_ranked_rows(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        class_id = uuid.uuid4()
        period_id = uuid.uuid4()
        service._ensure_class_access = AsyncMock(
            return_value=(SimpleNamespace(id=class_id), SimpleNamespace(id=period_id))
        )
        service._build_live_metrics = AsyncMock(
            return_value={
                "ordered_records": [
                    {
                        "student_id": uuid.uuid4(),
                        "student_name": "Amina",
                        "weighted_average": MoroccanGrade.from_float(17.5),
                        "mention": "Très Bien",
                        "class_rank": 1,
                        "total_students": 2,
                    },
                    {
                        "student_id": uuid.uuid4(),
                        "student_name": "Bilal",
                        "weighted_average": MoroccanGrade.from_float(13.0),
                        "mention": "Assez Bien",
                        "class_rank": 2,
                        "total_students": 2,
                    },
                ]
            }
        )

        result = await service.compute_class_averages(
            class_id=class_id,
            period_id=period_id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert [row["class_rank"] for row in result] == [1, 2]
        assert repo_in_uow.save_student_period_average.await_count == 2
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_get_gradebook_filters_rows_to_visible_students(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("PAR")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        class_id = uuid.uuid4()
        period_id = uuid.uuid4()
        visible_student = uuid.uuid4()
        hidden_student = uuid.uuid4()
        category = make_category("Exam", 1.0, 0)
        assignment = SimpleNamespace(
            id=uuid.uuid4(),
            title="Fractions",
            total_points=20,
            due_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        class_room = SimpleNamespace(id=class_id, name="6A", school_id=auth.school_id)
        period = SimpleNamespace(
            id=period_id,
            label="Trimester 1",
            school_id=auth.school_id,
        )
        service._ensure_class_access = AsyncMock(return_value=(class_room, period))
        service._resolve_visible_student_ids = AsyncMock(return_value={visible_student})
        service._build_live_metrics = AsyncMock(
            return_value={
                "categories": [category],
                "assignments": [(assignment, category)],
                "assignment_scores": {
                    (visible_student, assignment.id): {
                        "score": 18.0,
                        "published_at": "2026-03-30T10:00:00+00:00",
                    }
                },
                "category_averages_by_student": {
                    visible_student: {category.id: 18.0},
                    hidden_student: {category.id: 12.0},
                },
                "ordered_records": [
                    {
                        "student_id": visible_student,
                        "student_name": "Amina",
                        "weighted_average": MoroccanGrade.from_float(18.0),
                        "mention": "Très Bien",
                        "class_rank": 1,
                        "total_students": 2,
                    },
                    {
                        "student_id": hidden_student,
                        "student_name": "Bilal",
                        "weighted_average": MoroccanGrade.from_float(12.0),
                        "mention": "Assez Bien",
                        "class_rank": 2,
                        "total_students": 2,
                    },
                ],
            }
        )

        result = await service.get_gradebook(
            class_id=class_id,
            period_id=period_id,
            auth=auth,
        )

        assert len(result["rows"]) == 1
        assert result["rows"][0]["student_id"] == str(visible_student)

    @pytest.mark.asyncio
    async def test_get_student_transcript_combines_cached_and_live_periods(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        student_id = uuid.uuid4()
        academic_year_id = uuid.uuid4()
        service.erp_repo.get_academic_year.return_value = SimpleNamespace(
            id=academic_year_id,
            school_id=auth.school_id,
        )
        service.repo.get_user.return_value = SimpleNamespace(
            id=student_id,
            school_id=auth.school_id,
        )
        cached_class = SimpleNamespace(
            id=uuid.uuid4(), name="6A", school_id=auth.school_id
        )
        cached_period = SimpleNamespace(
            id=uuid.uuid4(),
            label="T1",
            date_start=date(2026, 9, 1),
        )
        cached_average = SimpleNamespace(
            weighted_average=16.5,
            mention="Très Bien",
            class_rank=1,
            total_students=25,
            computed_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        )
        live_class = SimpleNamespace(
            id=uuid.uuid4(), name="6B", school_id=auth.school_id
        )
        live_period = SimpleNamespace(
            id=uuid.uuid4(),
            label="T2",
            date_start=date(2027, 1, 5),
        )
        service.gradebook_repo.get_student_transcript.return_value = [
            (cached_average, cached_period, cached_class)
        ]
        service.gradebook_repo.list_student_period_enrollments.return_value = [
            (SimpleNamespace(id=uuid.uuid4()), live_class, live_period)
        ]
        service._build_live_metrics = AsyncMock(
            return_value={
                "ranked_by_student": {
                    student_id: {
                        "weighted_average": MoroccanGrade.from_float(14.0),
                        "mention": "Bien",
                        "class_rank": 3,
                        "total_students": 24,
                    }
                }
            }
        )

        result = await service.get_student_transcript(
            student_id=student_id,
            academic_year_id=academic_year_id,
            auth=auth,
        )

        assert [period["period_label"] for period in result["periods"]] == ["T1", "T2"]
        assert result["periods"][0]["computed_at"] is not None
        assert result["periods"][1]["computed_at"] is None
