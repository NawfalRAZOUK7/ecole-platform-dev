"""Feature toggle service."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.feature_flags import invalidate_feature_cache
from app.models.feature import FeatureToggle
from app.repositories.feature import FeatureRepository
from app.services.audit import AuditService


def _toggle_to_response(toggle: FeatureToggle) -> dict:
    return {
        "id": str(toggle.id),
        "feature_key": toggle.feature_key,
        "display_name": toggle.display_name,
        "description": toggle.description,
        "enabled_globally": toggle.enabled_globally,
        "enabled_school_ids": toggle.enabled_school_ids or [],
        "enabled_role_codes": toggle.enabled_role_codes or [],
        "created_at": toggle.created_at.isoformat() if toggle.created_at else None,
        "updated_at": toggle.updated_at.isoformat() if toggle.updated_at else None,
    }


def _toggle_snapshot(toggle: FeatureToggle) -> dict:
    return {
        "id": str(toggle.id),
        "feature_key": toggle.feature_key,
        "enabled_globally": toggle.enabled_globally,
        "enabled_school_ids": toggle.enabled_school_ids or [],
        "enabled_role_codes": toggle.enabled_role_codes or [],
    }


def _is_toggle_active(
    toggle: FeatureToggle,
    *,
    school_id: uuid.UUID,
    role_code: str,
) -> bool:
    if toggle.enabled_globally:
        return True
    if str(school_id) in (toggle.enabled_school_ids or []):
        return True
    if role_code in (toggle.enabled_role_codes or []):
        return True
    return False


class FeatureService:
    """Business logic for feature toggle evaluation and CRUD."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = FeatureRepository(db)
        self.audit = AuditService(db)

    async def get_active_features(
        self,
        *,
        school_id: uuid.UUID,
        role_code: str,
    ) -> dict:
        toggles = await self.repo.list_toggles()
        return {
            "features": [
                toggle.feature_key
                for toggle in toggles
                if _is_toggle_active(toggle, school_id=school_id, role_code=role_code)
            ]
        }

    async def create_feature_toggle(
        self,
        *,
        feature_key: str,
        display_name: str,
        description: str | None,
        enabled_globally: bool,
        enabled_school_ids: list[str],
        enabled_role_codes: list[str],
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> dict:
        existing = await self.repo.get_toggle_by_feature_key(feature_key)
        if existing is not None:
            raise ConflictError(
                f"Feature toggle '{feature_key}' already exists",
                error_code="ERR-FEATURE-409",
            )

        toggle = await self.repo.create_toggle(
            FeatureToggle(
                feature_key=feature_key,
                display_name=display_name,
                description=description,
                enabled_globally=enabled_globally,
                enabled_school_ids=enabled_school_ids,
                enabled_role_codes=enabled_role_codes,
            )
        )
        await self.audit.log_event(
            school_id=school_id,
            actor_id=actor_id,
            action_type="feature_toggle.create",
            outcome="success",
            target_type="feature_toggle",
            target_id=toggle.id,
            entity_after=_toggle_snapshot(toggle),
        )
        await self.db.commit()
        return _toggle_to_response(toggle)

    async def list_feature_toggles(self) -> list[dict]:
        toggles = await self.repo.list_toggles()
        return [_toggle_to_response(toggle) for toggle in toggles]

    async def get_feature_toggle(self, toggle_id: uuid.UUID) -> dict:
        toggle = await self.repo.get_toggle_by_id(toggle_id)
        if toggle is None:
            raise NotFoundError("Feature toggle not found", error_code="ERR-FEATURE-404")
        return _toggle_to_response(toggle)

    async def update_feature_toggle(
        self,
        *,
        toggle_id: uuid.UUID,
        display_name: str | None,
        description: str | None,
        enabled_globally: bool | None,
        enabled_school_ids: list[str] | None,
        enabled_role_codes: list[str] | None,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> dict:
        toggle = await self.repo.get_toggle_by_id(toggle_id)
        if toggle is None:
            raise NotFoundError("Feature toggle not found", error_code="ERR-FEATURE-404")

        before = _toggle_snapshot(toggle)
        if display_name is not None:
            toggle.display_name = display_name
        if description is not None:
            toggle.description = description
        if enabled_globally is not None:
            toggle.enabled_globally = enabled_globally
        if enabled_school_ids is not None:
            toggle.enabled_school_ids = enabled_school_ids
        if enabled_role_codes is not None:
            toggle.enabled_role_codes = enabled_role_codes

        await self.repo.save_toggle(toggle)
        await invalidate_feature_cache(toggle.feature_key)
        await self.audit.log_event(
            school_id=school_id,
            actor_id=actor_id,
            action_type="feature_toggle.update",
            outcome="success",
            target_type="feature_toggle",
            target_id=toggle.id,
            entity_before=before,
            entity_after=_toggle_snapshot(toggle),
        )
        await self.db.commit()
        return _toggle_to_response(toggle)

    async def delete_feature_toggle(
        self,
        *,
        toggle_id: uuid.UUID,
        school_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> dict:
        toggle = await self.repo.get_toggle_by_id(toggle_id)
        if toggle is None:
            raise NotFoundError("Feature toggle not found", error_code="ERR-FEATURE-404")

        before = _toggle_snapshot(toggle)
        feature_key = toggle.feature_key
        await self.repo.delete_toggle(toggle)
        await invalidate_feature_cache(feature_key)
        await self.audit.log_event(
            school_id=school_id,
            actor_id=actor_id,
            action_type="feature_toggle.delete",
            outcome="success",
            target_type="feature_toggle",
            target_id=toggle_id,
            entity_before=before,
        )
        await self.db.commit()
        return {"deleted": True, "feature_key": feature_key}
