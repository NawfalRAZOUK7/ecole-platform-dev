"""Unit tests for app/core/feature_flags.py — full branch coverage.

Strategy:
- Mock redis_client with AsyncMock to avoid real Redis.
- Mock AsyncSession to avoid DB dependency.
- Test _evaluate_toggle (pure), cache helpers, _load_toggle, is_feature_enabled,
  get_active_features, RequiresFeature, and invalidation helpers.
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError
from app.core.feature_flags import (
    FEATURE_CACHE_PREFIX,
    FEATURE_CACHE_TTL,
    RequiresFeature,
    _cache_key,
    _evaluate_toggle,
    _get_cached_toggle,
    _load_toggle,
    _set_cached_toggle,
    get_active_features,
    invalidate_all_feature_cache,
    invalidate_feature_cache,
    is_feature_enabled,
    requires_feature,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth(role: str = "teacher", school_id: uuid.UUID | None = None) -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=school_id or uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


def _toggle_data(
    key: str = "my_feature",
    globally: bool = False,
    school_ids: list[str] | None = None,
    role_codes: list[str] | None = None,
) -> dict:
    return {
        "feature_key": key,
        "enabled_globally": globally,
        "enabled_school_ids": school_ids or [],
        "enabled_role_codes": role_codes or [],
    }


def _mock_toggle_model(
    key: str,
    globally: bool = False,
    school_ids: list[str] | None = None,
    role_codes: list[str] | None = None,
):
    t = MagicMock()
    t.feature_key = key
    t.enabled_globally = globally
    t.enabled_school_ids = school_ids
    t.enabled_role_codes = role_codes
    return t


# ---------------------------------------------------------------------------
# _cache_key
# ---------------------------------------------------------------------------


def test_cache_key_has_prefix():
    key = _cache_key("my_feature")
    assert key == f"{FEATURE_CACHE_PREFIX}my_feature"


def test_cache_key_different_features_differ():
    assert _cache_key("feat_a") != _cache_key("feat_b")


# ---------------------------------------------------------------------------
# _evaluate_toggle — pure function, all 4 branches
# ---------------------------------------------------------------------------


def test_evaluate_globally_enabled():
    data = _toggle_data(globally=True)
    assert _evaluate_toggle(data) is True


def test_evaluate_globally_disabled_no_context():
    data = _toggle_data(globally=False)
    assert _evaluate_toggle(data) is False


def test_evaluate_school_id_match():
    sid = uuid.uuid4()
    data = _toggle_data(globally=False, school_ids=[str(sid)])
    assert _evaluate_toggle(data, school_id=sid) is True


def test_evaluate_school_id_no_match():
    data = _toggle_data(globally=False, school_ids=[str(uuid.uuid4())])
    assert _evaluate_toggle(data, school_id=uuid.uuid4()) is False


def test_evaluate_school_id_none_skipped():
    data = _toggle_data(globally=False, school_ids=["some-id"])
    assert _evaluate_toggle(data, school_id=None) is False


def test_evaluate_role_code_match():
    data = _toggle_data(globally=False, role_codes=["admin"])
    assert _evaluate_toggle(data, role_code="admin") is True


def test_evaluate_role_code_no_match():
    data = _toggle_data(globally=False, role_codes=["admin"])
    assert _evaluate_toggle(data, role_code="teacher") is False


def test_evaluate_role_code_none_skipped():
    data = _toggle_data(globally=False, role_codes=["admin"])
    assert _evaluate_toggle(data, role_code=None) is False


def test_evaluate_school_match_trumps_role_miss():
    sid = uuid.uuid4()
    data = _toggle_data(globally=False, school_ids=[str(sid)], role_codes=["admin"])
    assert _evaluate_toggle(data, school_id=sid, role_code="teacher") is True


def test_evaluate_globally_enabled_ignores_context():
    data = _toggle_data(globally=True, school_ids=[], role_codes=[])
    assert _evaluate_toggle(data, school_id=uuid.uuid4(), role_code="student") is True


# ---------------------------------------------------------------------------
# _get_cached_toggle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_cached_toggle_hit():
    payload = _toggle_data("feat", globally=True)
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(payload)

    with patch("app.core.feature_flags.redis_client", mock_redis):
        result = await _get_cached_toggle("feat")

    assert result == payload
    mock_redis.get.assert_awaited_once_with("feature_toggle:feat")


@pytest.mark.asyncio
async def test_get_cached_toggle_miss_returns_none():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("app.core.feature_flags.redis_client", mock_redis):
        result = await _get_cached_toggle("missing_feat")

    assert result is None


@pytest.mark.asyncio
async def test_get_cached_toggle_redis_error_returns_none():
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = ConnectionError("redis down")

    with patch("app.core.feature_flags.redis_client", mock_redis):
        result = await _get_cached_toggle("feat")

    assert result is None


# ---------------------------------------------------------------------------
# _set_cached_toggle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_cached_toggle_calls_redis_set():
    data = _toggle_data("feat")
    mock_redis = AsyncMock()

    with patch("app.core.feature_flags.redis_client", mock_redis):
        await _set_cached_toggle("feat", data)

    mock_redis.set.assert_awaited_once_with(
        "feature_toggle:feat",
        json.dumps(data),
        ex=FEATURE_CACHE_TTL,
    )


@pytest.mark.asyncio
async def test_set_cached_toggle_redis_error_is_swallowed():
    mock_redis = AsyncMock()
    mock_redis.set.side_effect = RuntimeError("connection refused")

    with patch("app.core.feature_flags.redis_client", mock_redis):
        # Should not raise
        await _set_cached_toggle("feat", _toggle_data())


# ---------------------------------------------------------------------------
# invalidate_feature_cache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_feature_cache_deletes_key():
    mock_redis = AsyncMock()

    with patch("app.core.feature_flags.redis_client", mock_redis):
        await invalidate_feature_cache("my_feature")

    mock_redis.delete.assert_awaited_once_with("feature_toggle:my_feature")


@pytest.mark.asyncio
async def test_invalidate_feature_cache_redis_error_swallowed():
    mock_redis = AsyncMock()
    mock_redis.delete.side_effect = ConnectionError("redis down")

    with patch("app.core.feature_flags.redis_client", mock_redis):
        await invalidate_feature_cache("my_feature")  # must not raise


# ---------------------------------------------------------------------------
# invalidate_all_feature_cache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_all_feature_cache_deletes_all_keys():
    mock_db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = ["feat_a", "feat_b"]
    mock_db.execute.return_value = result

    deleted = []

    async def fake_delete(key):
        deleted.append(key)

    mock_redis = AsyncMock()
    mock_redis.delete.side_effect = fake_delete

    with patch("app.core.feature_flags.redis_client", mock_redis):
        await invalidate_all_feature_cache(mock_db)

    assert "feature_toggle:feat_a" in deleted
    assert "feature_toggle:feat_b" in deleted


@pytest.mark.asyncio
async def test_invalidate_all_feature_cache_empty_db():
    mock_db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = result

    mock_redis = AsyncMock()

    with patch("app.core.feature_flags.redis_client", mock_redis):
        await invalidate_all_feature_cache(mock_db)

    mock_redis.delete.assert_not_awaited()


# ---------------------------------------------------------------------------
# _load_toggle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_toggle_from_cache():
    data = _toggle_data("feat", globally=True)
    mock_redis = AsyncMock()
    mock_redis.get.return_value = json.dumps(data)
    mock_db = AsyncMock()

    with patch("app.core.feature_flags.redis_client", mock_redis):
        result = await _load_toggle("feat", mock_db)

    assert result == data
    mock_db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_load_toggle_cache_miss_db_hit():
    school_id = str(uuid.uuid4())
    toggle = _mock_toggle_model("feat_b", globally=False, school_ids=[school_id])
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # cache miss
    mock_redis.set = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = toggle
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    with patch("app.core.feature_flags.redis_client", mock_redis):
        result = await _load_toggle("feat_b", mock_db)

    assert result is not None
    assert result["feature_key"] == "feat_b"
    assert result["enabled_school_ids"] == [school_id]
    # Should have cached the result
    mock_redis.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_load_toggle_cache_miss_db_miss_returns_none():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    with patch("app.core.feature_flags.redis_client", mock_redis):
        result = await _load_toggle("nonexistent", mock_db)

    assert result is None


@pytest.mark.asyncio
async def test_load_toggle_model_with_none_lists_defaulted():
    """toggle.enabled_school_ids = None → should default to []."""
    toggle = _mock_toggle_model(
        "feat_c", globally=False, school_ids=None, role_codes=None
    )
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = toggle
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    with patch("app.core.feature_flags.redis_client", mock_redis):
        result = await _load_toggle("feat_c", mock_db)

    assert result["enabled_school_ids"] == []
    assert result["enabled_role_codes"] == []


# ---------------------------------------------------------------------------
# is_feature_enabled
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_feature_enabled_globally_true():
    data = _toggle_data(globally=True)
    mock_db = AsyncMock()

    with patch("app.core.feature_flags._load_toggle", AsyncMock(return_value=data)):
        result = await is_feature_enabled("feat", mock_db)

    assert result is True


@pytest.mark.asyncio
async def test_is_feature_enabled_toggle_not_found_returns_false():
    mock_db = AsyncMock()

    with patch("app.core.feature_flags._load_toggle", AsyncMock(return_value=None)):
        result = await is_feature_enabled("nonexistent", mock_db)

    assert result is False


@pytest.mark.asyncio
async def test_is_feature_enabled_school_context():
    sid = uuid.uuid4()
    data = _toggle_data(globally=False, school_ids=[str(sid)])
    mock_db = AsyncMock()

    with patch("app.core.feature_flags._load_toggle", AsyncMock(return_value=data)):
        assert await is_feature_enabled("feat", mock_db, school_id=sid) is True
        assert (
            await is_feature_enabled("feat", mock_db, school_id=uuid.uuid4()) is False
        )


@pytest.mark.asyncio
async def test_is_feature_enabled_role_context():
    data = _toggle_data(globally=False, role_codes=["admin"])
    mock_db = AsyncMock()

    with patch("app.core.feature_flags._load_toggle", AsyncMock(return_value=data)):
        assert await is_feature_enabled("feat", mock_db, role_code="admin") is True
        assert await is_feature_enabled("feat", mock_db, role_code="student") is False


# ---------------------------------------------------------------------------
# get_active_features
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_active_features_returns_enabled_keys():
    sid = uuid.uuid4()
    toggles = [
        _mock_toggle_model("feat_global", globally=True),
        _mock_toggle_model("feat_school", globally=False, school_ids=[str(sid)]),
        _mock_toggle_model("feat_disabled", globally=False),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = toggles
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()

    with patch("app.core.feature_flags.redis_client", mock_redis):
        active = await get_active_features(mock_db, school_id=sid)

    assert "feat_global" in active
    assert "feat_school" in active
    assert "feat_disabled" not in active


@pytest.mark.asyncio
async def test_get_active_features_empty_db():
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    mock_redis = AsyncMock()

    with patch("app.core.feature_flags.redis_client", mock_redis):
        active = await get_active_features(mock_db)

    assert active == []


@pytest.mark.asyncio
async def test_get_active_features_caches_each_toggle():
    toggles = [
        _mock_toggle_model("feat_a", globally=True),
        _mock_toggle_model("feat_b", globally=True),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = toggles
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()

    with patch("app.core.feature_flags.redis_client", mock_redis):
        await get_active_features(mock_db)

    assert mock_redis.set.await_count == 2


@pytest.mark.asyncio
async def test_get_active_features_by_role():
    toggles = [
        _mock_toggle_model("feat_admin", globally=False, role_codes=["admin"]),
        _mock_toggle_model("feat_teacher", globally=False, role_codes=["teacher"]),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = toggles
    mock_db = AsyncMock()
    mock_db.execute.return_value = mock_result

    mock_redis = AsyncMock()
    mock_redis.set = AsyncMock()

    with patch("app.core.feature_flags.redis_client", mock_redis):
        active = await get_active_features(mock_db, role_code="admin")

    assert "feat_admin" in active
    assert "feat_teacher" not in active


# ---------------------------------------------------------------------------
# RequiresFeature
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_requires_feature_enabled_returns_auth():
    auth = _auth(role="admin")
    mock_db = AsyncMock()
    guard = RequiresFeature("my_feature")

    with patch(
        "app.core.feature_flags.is_feature_enabled", AsyncMock(return_value=True)
    ):
        result = await guard(auth=auth, db=mock_db)

    assert result is auth


@pytest.mark.asyncio
async def test_requires_feature_disabled_raises_not_found():
    auth = _auth(role="teacher")
    mock_db = AsyncMock()
    guard = RequiresFeature("disabled_feature")

    with patch(
        "app.core.feature_flags.is_feature_enabled", AsyncMock(return_value=False)
    ):
        with pytest.raises(NotFoundError):
            await guard(auth=auth, db=mock_db)


@pytest.mark.asyncio
async def test_requires_feature_passes_school_and_role():
    school_id = uuid.uuid4()
    auth = _auth(role="admin", school_id=school_id)
    mock_db = AsyncMock()
    guard = RequiresFeature("scoped_feature")

    captured = {}

    async def fake_is_enabled(key, db, school_id=None, role_code=None):
        captured["key"] = key
        captured["school_id"] = school_id
        captured["role_code"] = role_code
        return True

    with patch("app.core.feature_flags.is_feature_enabled", fake_is_enabled):
        await guard(auth=auth, db=mock_db)

    assert captured["key"] == "scoped_feature"
    assert captured["school_id"] == school_id
    assert captured["role_code"] == "admin"


def test_requires_feature_factory():
    guard = requires_feature("some_feature")
    assert isinstance(guard, RequiresFeature)
    assert guard.feature_key == "some_feature"


def test_requires_feature_init_stores_key():
    guard = RequiresFeature("test_key")
    assert guard.feature_key == "test_key"
