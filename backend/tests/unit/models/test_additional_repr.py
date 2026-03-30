"""Additional repr coverage for low-touch models."""

from __future__ import annotations

import uuid

import pytest

from app.models.audit import AuditLog, _short_id
from app.models.feature import FeatureToggle


class TestFeatureToggleRepr:
    @pytest.mark.parametrize("enabled_globally", [False, True])
    def test_repr_includes_key_and_global_flag(self, enabled_globally: bool):
        feature = FeatureToggle(
            feature_key="billing.payment_plans",
            display_name="Payment plans",
            enabled_globally=enabled_globally,
        )
        feature.id = uuid.uuid4()

        rendered = repr(feature)

        assert str(feature.id)[:8] in rendered
        assert "billing.payment_plans" in rendered
        assert f"enabled_globally={enabled_globally}" in rendered


class TestAuditHelpers:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (None, "None"),
            (uuid.UUID("11111111-2222-3333-4444-555555555555"), "11111111"),
            ("abcdef123456", "abcdef12"),
        ],
    )
    def test_short_id_handles_none_uuid_and_strings(self, value: object | None, expected: str):
        assert _short_id(value) == expected

    @pytest.mark.parametrize("target_type", [None, "invoice", "payment_plan"])
    def test_audit_log_repr_includes_action_and_target_type(self, target_type: str | None):
        audit_log = AuditLog(
            school_id=uuid.uuid4(),
            action_type="billing.payment_plan.create",
            outcome="success",
            target_type=target_type,
        )
        audit_log.id = uuid.uuid4()

        rendered = repr(audit_log)

        assert str(audit_log.id)[:8] in rendered
        assert "billing.payment_plan.create" in rendered
        assert f"target_type={target_type}" in rendered
