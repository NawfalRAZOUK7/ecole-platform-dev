"""Feature flag evaluation with Redis caching — Phase 11E.

Reference: Phase 11E — Feature Toggles
Provides:
  - is_feature_enabled(key, school_id, role_code) — check if a feature is ON
  - get_active_features(school_id, role_code) — list all active feature keys
  - RequiresFeature(key) — FastAPI dependency guard (returns 404 if disabled)
  - invalidate_feature_cache(key) — bust cache after toggle update

Cache strategy: Redis with 1-minute TTL per feature key.
Graceful degradation: if Redis is unavailable, fall back to DB query.
"""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user
from app.core.exceptions import NotFoundError
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

FEATURE_CACHE_PREFIX = "feature_toggle:"
FEATURE_CACHE_TTL = 60  # 1 minute


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------
def _cache_key(feature_key: str) -> str:
    return f"{FEATURE_CACHE_PREFIX}{feature_key}"


async def _get_cached_toggle(feature_key: str) -> dict | None:
    """Try to retrieve a cached feature toggle from Redis."""
    try:
        raw = await redis_client.get(_cache_key(feature_key))
        if raw is not None:
            return json.loads(raw)
    except Exception:
        logger.debug("Redis unavailable for feature cache read: %s", feature_key)
    return None


async def _set_cached_toggle(feature_key: str, data: dict) -> None:
    """Cache a feature toggle in Redis."""
    try:
        await redis_client.set(
            _cache_key(feature_key),
            json.dumps(data),
            ex=FEATURE_CACHE_TTL,
        )
    except Exception:
        logger.debug("Redis unavailable for feature cache write: %s", feature_key)


async def invalidate_feature_cache(feature_key: str) -> None:
    """Bust cache for a specific feature toggle."""
    try:
        await redis_client.delete(_cache_key(feature_key))
    except Exception:
        logger.debug(
            "Redis unavailable for feature cache invalidation: %s", feature_key
        )


async def invalidate_all_feature_cache(db: AsyncSession) -> None:
    """Bust cache for all feature toggles."""
    from app.models.feature import FeatureToggle

    result = await db.execute(select(FeatureToggle.feature_key))
    keys = result.scalars().all()
    for key in keys:
        await invalidate_feature_cache(key)


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------
async def _load_toggle(feature_key: str, db: AsyncSession) -> dict | None:
    """Load toggle from cache or DB. Returns dict or None if not found."""
    # Try cache first
    cached = await _get_cached_toggle(feature_key)
    if cached is not None:
        return cached

    # Fall back to DB
    from app.models.feature import FeatureToggle

    result = await db.execute(
        select(FeatureToggle).where(FeatureToggle.feature_key == feature_key)
    )
    toggle = result.scalar_one_or_none()
    if toggle is None:
        return None

    data = {
        "feature_key": toggle.feature_key,
        "enabled_globally": toggle.enabled_globally,
        "enabled_school_ids": toggle.enabled_school_ids or [],
        "enabled_role_codes": toggle.enabled_role_codes or [],
    }

    # Cache it
    await _set_cached_toggle(feature_key, data)
    return data


def _evaluate_toggle(
    toggle_data: dict,
    school_id: uuid.UUID | None = None,
    role_code: str | None = None,
) -> bool:
    """Evaluate whether a feature is enabled for the given context.

    Scoping logic (evaluated in order):
    1. enabled_globally → ON for everyone
    2. school_id in enabled_school_ids → ON for that school
    3. role_code in enabled_role_codes → ON for that role
    4. Otherwise → OFF
    """
    if toggle_data["enabled_globally"]:
        return True

    if school_id and str(school_id) in toggle_data.get("enabled_school_ids", []):
        return True

    if role_code and role_code in toggle_data.get("enabled_role_codes", []):
        return True

    return False


async def is_feature_enabled(
    feature_key: str,
    db: AsyncSession,
    school_id: uuid.UUID | None = None,
    role_code: str | None = None,
) -> bool:
    """Check if a feature is enabled for the given school/role context.

    Returns False if the feature toggle doesn't exist (fail-closed).
    """
    toggle_data = await _load_toggle(feature_key, db)
    if toggle_data is None:
        return False
    return _evaluate_toggle(toggle_data, school_id, role_code)


async def get_active_features(
    db: AsyncSession,
    school_id: uuid.UUID | None = None,
    role_code: str | None = None,
) -> list[str]:
    """Return list of active feature keys for the given school/role context."""
    from app.models.feature import FeatureToggle

    result = await db.execute(select(FeatureToggle))
    toggles = result.scalars().all()

    active = []
    for toggle in toggles:
        data = {
            "feature_key": toggle.feature_key,
            "enabled_globally": toggle.enabled_globally,
            "enabled_school_ids": toggle.enabled_school_ids or [],
            "enabled_role_codes": toggle.enabled_role_codes or [],
        }
        # Also refresh cache while we're at it
        await _set_cached_toggle(toggle.feature_key, data)

        if _evaluate_toggle(data, school_id, role_code):
            active.append(toggle.feature_key)

    return active


# ---------------------------------------------------------------------------
# RequiresFeature dependency guard
# ---------------------------------------------------------------------------
class RequiresFeature:
    """FastAPI dependency that checks if a feature toggle is enabled.

    Usage:
        @router.get("/foo", dependencies=[Depends(RequiresFeature("messaging"))])
        async def foo(...): ...

    Or in endpoint signature:
        async def foo(auth: AuthContext = Depends(RequiresFeature("messaging"))): ...

    Returns 404 (not 403) to avoid leaking feature existence.
    """

    def __init__(self, feature_key: str) -> None:
        self.feature_key = feature_key

    async def __call__(
        self,
        auth: AuthContext = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> AuthContext:
        enabled = await is_feature_enabled(
            self.feature_key, db, school_id=auth.school_id, role_code=auth.role
        )
        if not enabled:
            raise NotFoundError(
                "Resource not found",
                error_code="ERR-FEATURE-404",
            )
        return auth


def requires_feature(feature_key: str) -> RequiresFeature:
    """Create a RequiresFeature dependency for the given feature key."""
    return RequiresFeature(feature_key)
