"""Unit tests for app/services/academic/progress.py — full branch coverage."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.core.permissions import ADM, DIR, PAR, STD, TCH
import app.services.academic.progress as progress_module
from app.services.academic.progress import (
    CACHE_TTL,
    ProgressService,
    _cache_key,
    _get_cached,
    _set_cached,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth(role: str = ADM, user_id=None, school_id=None) -> AuthContext:
    return AuthContext(
        user_id=user_id or uuid.uuid4(),
        role=role,
        school_id=school_id or uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


def _make_service() -> tuple[ProgressService, AsyncMock]:
    db = AsyncMock()
    svc = ProgressService(db)
    svc.repo = AsyncMock()
    return svc, svc.repo


# ---------------------------------------------------------------------------
# _cache_key
# ---------------------------------------------------------------------------


def test_cache_key_format():
    sid = uuid.uuid4()
    key = _cache_key("grades", sid, "school1")
    assert key.startswith("progress:grades:")
    assert str(sid) in key


def test_cache_key_different_prefixes():
    sid = uuid.uuid4()
    assert _cache_key("grades", sid) != _cache_key("content", sid)


# ---------------------------------------------------------------------------
# _get_cached / _set_cached
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_cached_hit():
    data = {"key": "value"}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(data)
    with patch.object(progress_module, "redis_client", mock_redis):
        result = await _get_cached("test:key")
    assert result == data


@pytest.mark.asyncio
async def test_get_cached_miss_returns_none():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    with patch.object(progress_module, "redis_client", mock_redis):
        result = await _get_cached("test:key")
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_exception_returns_none():
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = ConnectionError("redis down")
    with patch.object(progress_module, "redis_client", mock_redis):
        result = await _get_cached("test:key")
    assert result is None


@pytest.mark.asyncio
async def test_set_cached_writes_json():
    data = {"labels": ["Jan"], "value": 42}
    mock_redis = AsyncMock()
    with patch.object(progress_module, "redis_client", mock_redis):
        await _set_cached("test:key", data)
    mock_redis.set.assert_awaited_once()
    args = mock_redis.set.call_args
    assert args.args[0] == "test:key"
    assert args.kwargs.get("ex") == CACHE_TTL


@pytest.mark.asyncio
async def test_set_cached_exception_swallowed():
    mock_redis = AsyncMock()
    mock_redis.set.side_effect = ConnectionError("redis down")
    with patch.object(progress_module, "redis_client", mock_redis):
        await _set_cached("test:key", {"x": 1})  # must not raise


# ---------------------------------------------------------------------------
# ProgressService.verify_student_access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_student_access_admin_valid():
    svc, repo = _make_service()
    sid = uuid.uuid4()
    school_id = uuid.uuid4()
    repo.get_student_school_id.return_value = school_id
    auth = _auth(ADM, school_id=school_id)
    await svc.verify_student_access(student_id=sid, auth=auth)
    repo.get_student_school_id.assert_awaited_once_with(sid)


@pytest.mark.asyncio
async def test_verify_student_access_admin_student_not_found():
    svc, repo = _make_service()
    repo.get_student_school_id.return_value = None
    with pytest.raises(NotFoundError, match="Student not found"):
        await svc.verify_student_access(student_id=uuid.uuid4(), auth=_auth(ADM))


@pytest.mark.asyncio
async def test_verify_student_access_dir_valid():
    svc, repo = _make_service()
    school_id = uuid.uuid4()
    repo.get_student_school_id.return_value = school_id
    auth = _auth(DIR, school_id=school_id)
    await svc.verify_student_access(student_id=uuid.uuid4(), auth=auth)


@pytest.mark.asyncio
async def test_verify_student_access_std_self_ok():
    svc, repo = _make_service()
    uid = uuid.uuid4()
    auth = _auth(STD, user_id=uid)
    await svc.verify_student_access(student_id=uid, auth=auth)


@pytest.mark.asyncio
async def test_verify_student_access_std_other_denied():
    svc, repo = _make_service()
    auth = _auth(STD, user_id=uuid.uuid4())
    with pytest.raises(NotFoundError):
        await svc.verify_student_access(student_id=uuid.uuid4(), auth=auth)


@pytest.mark.asyncio
async def test_verify_student_access_par_child_ok():
    svc, repo = _make_service()
    child_id = uuid.uuid4()
    parent_id = uuid.uuid4()
    school_id = uuid.uuid4()
    repo.list_parent_child_ids.return_value = [child_id]
    auth = _auth(PAR, user_id=parent_id, school_id=school_id)

    with patch(
        "app.services.academic.progress.verify_parent_child_ownership"
    ) as mock_verify:
        await svc.verify_student_access(student_id=child_id, auth=auth)

    mock_verify.assert_called_once_with(child_id, [child_id])


@pytest.mark.asyncio
async def test_verify_student_access_tch_enrolled_ok():
    svc, repo = _make_service()
    student_id = uuid.uuid4()
    class_ids = [uuid.uuid4()]
    repo.list_teacher_class_ids.return_value = class_ids
    repo.student_is_enrolled_in_classes.return_value = True
    auth = _auth(TCH)
    await svc.verify_student_access(student_id=student_id, auth=auth)
    repo.student_is_enrolled_in_classes.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_student_access_tch_not_enrolled_raises():
    svc, repo = _make_service()
    repo.list_teacher_class_ids.return_value = [uuid.uuid4()]
    repo.student_is_enrolled_in_classes.return_value = False
    auth = _auth(TCH)
    with pytest.raises(NotFoundError):
        await svc.verify_student_access(student_id=uuid.uuid4(), auth=auth)


@pytest.mark.asyncio
async def test_verify_student_access_unknown_role_raises():
    svc, repo = _make_service()
    auth = _auth("UNKNOWN")
    with pytest.raises(NotFoundError):
        await svc.verify_student_access(student_id=uuid.uuid4(), auth=auth)


# ---------------------------------------------------------------------------
# ProgressService.verify_class_access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_class_access_found_non_teacher():
    svc, repo = _make_service()
    school_id = uuid.uuid4()
    class_id = uuid.uuid4()
    repo.get_class_school_id.return_value = school_id
    auth = _auth(ADM, school_id=school_id)

    with patch("app.services.academic.progress.verify_school_boundary"):
        await svc.verify_class_access(class_id=class_id, auth=auth)


@pytest.mark.asyncio
async def test_verify_class_access_not_found_raises():
    svc, repo = _make_service()
    repo.get_class_school_id.return_value = None
    with pytest.raises(NotFoundError, match="Class not found"):
        await svc.verify_class_access(class_id=uuid.uuid4(), auth=_auth(ADM))


@pytest.mark.asyncio
async def test_verify_class_access_teacher_checks_assignment():
    svc, repo = _make_service()
    school_id = uuid.uuid4()
    class_id = uuid.uuid4()
    class_ids = [class_id]
    repo.get_class_school_id.return_value = school_id
    repo.list_teacher_class_ids.return_value = class_ids
    auth = _auth(TCH, school_id=school_id)

    with (
        patch("app.services.academic.progress.verify_school_boundary"),
        patch("app.services.academic.progress.verify_teacher_assignment") as mock_ta,
    ):
        await svc.verify_class_access(class_id=class_id, auth=auth)

    mock_ta.assert_called_once_with(class_id, class_ids)


# ---------------------------------------------------------------------------
# get_grade_trends
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_grade_trends_cache_miss_fetches_and_caches():
    svc, repo = _make_service()
    sid = uuid.uuid4()
    school_id = uuid.uuid4()
    rows = [{"month": "2024-01", "avg_score": 14.5, "count": 3}]
    repo.list_grade_trend_rows.return_value = rows

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # cache miss

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_grade_trends(sid, school_id)

    assert result["labels"] == ["2024-01"]
    assert result["datasets"][0]["data"] == [14.5]
    mock_redis.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_grade_trends_cache_hit_returns_cached():
    svc, repo = _make_service()
    cached_data = {"labels": ["2024-01"], "datasets": []}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(cached_data)

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_grade_trends(uuid.uuid4(), uuid.uuid4())

    assert result == cached_data
    repo.list_grade_trend_rows.assert_not_awaited()


# ---------------------------------------------------------------------------
# get_content_completion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_content_completion_with_data():
    svc, repo = _make_service()
    repo.get_content_completion_counts.return_value = {
        "completed": 5,
        "in_progress": 2,
        "not_started": 3,
    }
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_content_completion(uuid.uuid4(), uuid.uuid4())

    assert result["summary"]["total"] == 10
    assert result["summary"]["completion_rate"] == 50.0


@pytest.mark.asyncio
async def test_get_content_completion_zero_total():
    svc, repo = _make_service()
    repo.get_content_completion_counts.return_value = {
        "completed": 0,
        "in_progress": 0,
        "not_started": 0,
    }
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_content_completion(uuid.uuid4(), uuid.uuid4())

    assert result["summary"]["completion_rate"] == 0


@pytest.mark.asyncio
async def test_get_content_completion_cache_hit():
    svc, repo = _make_service()
    cached = {"labels": [], "datasets": [], "summary": {"total": 0}}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(cached)

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_content_completion(uuid.uuid4(), uuid.uuid4())

    assert result == cached
    repo.get_content_completion_counts.assert_not_awaited()


# ---------------------------------------------------------------------------
# get_activity_scores
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_activity_scores_cache_miss():
    svc, repo = _make_service()
    rows = [{"month": "2024-01", "avg_score": 80.0, "sessions": 4}]
    repo.list_activity_score_rows.return_value = rows
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_activity_scores(uuid.uuid4(), uuid.uuid4())

    assert result["labels"] == ["2024-01"]
    assert result["datasets"][0]["data"] == [80.0]


@pytest.mark.asyncio
async def test_get_activity_scores_cache_hit():
    svc, repo = _make_service()
    cached = {"labels": ["Jan"], "datasets": []}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(cached)

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_activity_scores(uuid.uuid4(), uuid.uuid4())

    assert result == cached


# ---------------------------------------------------------------------------
# get_attendance_rates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_attendance_rates_with_data():
    svc, repo = _make_service()
    repo.get_attendance_overview_counts.return_value = {
        "present": 20,
        "absent": 5,
        "excused": 2,
        "late": 3,
    }
    repo.list_attendance_monthly_rows.return_value = [
        {"month": "2024-01", "present_count": 20, "total_records": 25},
    ]
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_attendance_rates(uuid.uuid4(), uuid.uuid4())

    assert result["overview"]["summary"]["attendance_rate"] == 66.7
    assert result["trend"]["labels"] == ["2024-01"]


@pytest.mark.asyncio
async def test_get_attendance_rates_zero_total_records():
    svc, repo = _make_service()
    repo.get_attendance_overview_counts.return_value = {
        "present": 0,
        "absent": 0,
        "excused": 0,
        "late": 0,
    }
    repo.list_attendance_monthly_rows.return_value = [
        {"month": "2024-01", "present_count": 0, "total_records": 0},
    ]
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_attendance_rates(uuid.uuid4(), uuid.uuid4())

    assert result["overview"]["summary"]["attendance_rate"] == 0
    assert result["trend"]["datasets"][0]["data"] == [0]


@pytest.mark.asyncio
async def test_get_attendance_rates_cache_hit():
    svc, repo = _make_service()
    cached = {"overview": {}, "trend": {}}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(cached)

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_attendance_rates(uuid.uuid4(), uuid.uuid4())

    assert result == cached


# ---------------------------------------------------------------------------
# get_assessment_results
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_assessment_results_reverses_order():
    svc, repo = _make_service()
    rows = [
        {"title": "Math exam", "score": 15, "total_points": 20},
        {"title": "Science test", "score": 18, "total_points": 20},
    ]
    repo.list_assessment_result_rows.return_value = rows
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_assessment_results(uuid.uuid4(), uuid.uuid4())

    # Results should be reversed
    assert result["labels"][0] == "Science test"
    assert result["labels"][1] == "Math exam"


@pytest.mark.asyncio
async def test_get_assessment_results_cache_hit():
    svc, repo = _make_service()
    cached = {"labels": [], "datasets": []}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(cached)

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_assessment_results(uuid.uuid4(), uuid.uuid4())

    assert result == cached


# ---------------------------------------------------------------------------
# get_student_progress
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_student_progress_assembles_all_data():
    svc, repo = _make_service()
    sid = uuid.uuid4()
    school_id = uuid.uuid4()
    repo.get_student_name.return_value = "Yassine Alaoui"

    # Mock all sub-methods
    with patch.object(svc, "get_grade_trends", AsyncMock(return_value={"grades": []})):
        with patch.object(
            svc, "get_content_completion", AsyncMock(return_value={"content": []})
        ):
            with patch.object(
                svc, "get_activity_scores", AsyncMock(return_value={"activities": []})
            ):
                with patch.object(
                    svc,
                    "get_attendance_rates",
                    AsyncMock(return_value={"attendance": {}}),
                ):
                    with patch.object(
                        svc,
                        "get_assessment_results",
                        AsyncMock(return_value={"assessments": []}),
                    ):
                        mock_redis = AsyncMock()
                        mock_redis.get.return_value = None
                        with patch.object(progress_module, "redis_client", mock_redis):
                            result = await svc.get_student_progress(sid, school_id)

    assert result["student_id"] == str(sid)
    assert result["student_name"] == "Yassine Alaoui"
    assert "grade_trends" in result


@pytest.mark.asyncio
async def test_get_student_progress_default_name():
    svc, repo = _make_service()
    repo.get_student_name.return_value = None

    with patch.object(svc, "get_grade_trends", AsyncMock(return_value={})):
        with patch.object(svc, "get_content_completion", AsyncMock(return_value={})):
            with patch.object(svc, "get_activity_scores", AsyncMock(return_value={})):
                with patch.object(
                    svc, "get_attendance_rates", AsyncMock(return_value={})
                ):
                    with patch.object(
                        svc, "get_assessment_results", AsyncMock(return_value={})
                    ):
                        mock_redis = AsyncMock()
                        mock_redis.get.return_value = None
                        with patch.object(progress_module, "redis_client", mock_redis):
                            result = await svc.get_student_progress(
                                uuid.uuid4(), uuid.uuid4()
                            )

    assert result["student_name"] == "Élève"


@pytest.mark.asyncio
async def test_get_student_progress_cache_hit():
    svc, repo = _make_service()
    cached = {"student_id": "x", "student_name": "Test"}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(cached)

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_student_progress(uuid.uuid4(), uuid.uuid4())

    assert result == cached


# ---------------------------------------------------------------------------
# get_class_progress
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_class_progress_empty_class():
    svc, repo = _make_service()
    class_id = uuid.uuid4()
    school_id = uuid.uuid4()
    repo.get_class_info.return_value = ("6ème A", "2024-2025")
    repo.list_class_students.return_value = []
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_class_progress(class_id, school_id)

    assert result["student_count"] == 0
    assert result["students"] == []
    assert result["class_averages"]["grade_average"] is None


@pytest.mark.asyncio
async def test_get_class_progress_with_students():
    svc, repo = _make_service()
    class_id = uuid.uuid4()
    school_id = uuid.uuid4()
    sid1 = uuid.uuid4()
    sid2 = uuid.uuid4()
    repo.get_class_info.return_value = ("6ème B", "2024-2025")
    repo.list_class_students.return_value = [(sid1, "Alice"), (sid2, "Bob")]
    repo.get_grade_averages_for_students.return_value = {sid1: 14.0, sid2: None}
    repo.get_attendance_rates_for_students.return_value = {sid1: 90.0, sid2: 85.0}
    repo.get_content_completion_rates_for_students.return_value = {
        sid1: 60.0,
        sid2: 70.0,
    }
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_class_progress(class_id, school_id)

    assert result["student_count"] == 2
    assert len(result["students"]) == 2
    # Students sorted alphabetically
    assert result["students"][0]["student_name"] == "Alice"
    assert result["class_averages"]["grade_average"] == 14.0  # only sid1 has grade


@pytest.mark.asyncio
async def test_get_class_progress_class_info_none():
    svc, repo = _make_service()
    repo.get_class_info.return_value = None
    repo.list_class_students.return_value = []
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_class_progress(uuid.uuid4(), uuid.uuid4())

    assert result["class_name"] == "Classe"


@pytest.mark.asyncio
async def test_get_class_progress_cache_hit():
    svc, repo = _make_service()
    cached = {"class_id": "x", "students": []}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(cached)

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_class_progress(uuid.uuid4(), uuid.uuid4())

    assert result == cached


# ---------------------------------------------------------------------------
# get_children_progress
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_children_progress_no_children():
    svc, repo = _make_service()
    repo.list_children.return_value = []
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_children_progress(uuid.uuid4(), uuid.uuid4())

    assert result["child_count"] == 0
    assert result["children"] == []


@pytest.mark.asyncio
async def test_get_children_progress_with_children():
    svc, repo = _make_service()
    cid = uuid.uuid4()
    repo.list_children.return_value = [(cid, "Omar Benali")]
    repo.get_student_grade_average.return_value = 15.5
    repo.get_student_attendance_rate.return_value = 95.0
    repo.get_student_content_completion_rate.return_value = 80.0
    repo.get_latest_grade.return_value = {"subject": "Math", "score": 18}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_children_progress(uuid.uuid4(), uuid.uuid4())

    assert result["child_count"] == 1
    child = result["children"][0]
    assert child["student_name"] == "Omar Benali"
    assert child["grade_average"] == 15.5
    assert "charts" in result


@pytest.mark.asyncio
async def test_get_children_progress_grade_none():
    svc, repo = _make_service()
    cid = uuid.uuid4()
    repo.list_children.return_value = [(cid, "Sara")]
    repo.get_student_grade_average.return_value = None
    repo.get_student_attendance_rate.return_value = None
    repo.get_student_content_completion_rate.return_value = None
    repo.get_latest_grade.return_value = None
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_children_progress(uuid.uuid4(), uuid.uuid4())

    child = result["children"][0]
    assert child["grade_average"] is None


@pytest.mark.asyncio
async def test_get_children_progress_cache_hit():
    svc, repo = _make_service()
    cached = {"child_count": 0, "children": []}
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(cached)

    with patch.object(progress_module, "redis_client", mock_redis):
        result = await svc.get_children_progress(uuid.uuid4(), uuid.uuid4())

    assert result == cached


# ---------------------------------------------------------------------------
# get_student_progress_for_user / get_class_progress_for_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_student_progress_for_user_calls_verify_and_get():
    svc, repo = _make_service()
    uid = uuid.uuid4()
    school_id = uuid.uuid4()
    auth = _auth(STD, user_id=uid, school_id=school_id)
    expected = {"student_id": str(uid), "student_name": "Test"}

    with (
        patch.object(svc, "verify_student_access", AsyncMock()),
        patch.object(svc, "get_student_progress", AsyncMock(return_value=expected)),
    ):
        result = await svc.get_student_progress_for_user(student_id=uid, auth=auth)

    assert result == expected


@pytest.mark.asyncio
async def test_get_class_progress_for_user_calls_verify_and_get():
    svc, repo = _make_service()
    class_id = uuid.uuid4()
    school_id = uuid.uuid4()
    auth = _auth(ADM, school_id=school_id)
    expected = {"class_id": str(class_id)}

    with (
        patch.object(svc, "verify_class_access", AsyncMock()),
        patch.object(svc, "get_class_progress", AsyncMock(return_value=expected)),
    ):
        result = await svc.get_class_progress_for_user(class_id=class_id, auth=auth)

    assert result == expected


# ---------------------------------------------------------------------------
# get_my_progress
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_my_progress_std_ok():
    svc, repo = _make_service()
    uid = uuid.uuid4()
    school_id = uuid.uuid4()
    auth = _auth(STD, user_id=uid, school_id=school_id)
    expected = {"student_id": str(uid)}

    with patch.object(svc, "get_student_progress", AsyncMock(return_value=expected)):
        result = await svc.get_my_progress(auth=auth)

    assert result == expected


@pytest.mark.asyncio
async def test_get_my_progress_non_std_raises():
    svc, repo = _make_service()
    auth = _auth(TCH)
    with pytest.raises(ValidationError, match="students only"):
        await svc.get_my_progress(auth=auth)


# ---------------------------------------------------------------------------
# get_children_progress_for_parent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_children_progress_for_parent_ok():
    svc, repo = _make_service()
    uid = uuid.uuid4()
    school_id = uuid.uuid4()
    auth = _auth(PAR, user_id=uid, school_id=school_id)
    expected = {"child_count": 0, "children": []}

    with patch.object(svc, "get_children_progress", AsyncMock(return_value=expected)):
        result = await svc.get_children_progress_for_parent(auth=auth)

    assert result == expected


@pytest.mark.asyncio
async def test_get_children_progress_for_parent_non_par_raises():
    svc, repo = _make_service()
    auth = _auth(ADM)
    with pytest.raises(ValidationError, match="parents only"):
        await svc.get_children_progress_for_parent(auth=auth)
