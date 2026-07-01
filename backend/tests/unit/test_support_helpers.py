"""Self-tests for the tests/_support/ helper package.

Validates the builders and matchers (so the shared helpers are themselves under
test) and doubles as living documentation of how to use them.
"""

from __future__ import annotations

import uuid

import pytest

from app.core.dependencies import AuthContext
from app.models.onboarding import ApplicationType, SchoolApplication
from tests._support.builders import AuthContextBuilder, SchoolApplicationBuilder
from tests._support.matchers import (
    assert_activation_url,
    assert_error_envelope,
    assert_list_envelope,
    assert_success_envelope,
    assert_uuid,
    is_uuid,
)


class TestAuthContextBuilder:
    def test_defaults_produce_valid_context(self) -> None:
        auth = AuthContextBuilder().build()
        assert isinstance(auth, AuthContext)
        assert auth.role == "STD"
        assert isinstance(auth.user_id, uuid.UUID)

    def test_role_helpers(self) -> None:
        assert AuthContextBuilder().as_superadmin().build().role == "SUP"
        assert AuthContextBuilder().as_admin().build().role == "ADM"
        assert AuthContextBuilder().as_teacher().build().role == "TCH"

    def test_explicit_ids_are_used(self) -> None:
        uid, sid = uuid.uuid4(), uuid.uuid4()
        auth = AuthContextBuilder().with_user(uid).for_school(sid).build()
        assert auth.user_id == uid
        assert auth.school_id == sid

    def test_permissions_are_set(self) -> None:
        auth = AuthContextBuilder().with_permissions("a", "b").build()
        assert auth.permissions == {"a", "b"}


class TestSchoolApplicationBuilder:
    def test_payload_has_required_fields(self) -> None:
        payload = SchoolApplicationBuilder().micro_school().as_payload()
        assert {
            "applicant_name",
            "applicant_email",
            "org_name",
            "language",
        } <= payload.keys()

    def test_model_is_pending_application(self) -> None:
        model = SchoolApplicationBuilder().formal_school().as_model()
        assert isinstance(model, SchoolApplication)
        assert model.application_type == ApplicationType.FORMAL_SCHOOL.value

    def test_custom_email_is_respected(self) -> None:
        payload = SchoolApplicationBuilder().with_email("owner@x.ma").as_payload()
        assert payload["applicant_email"] == "owner@x.ma"

    def test_auto_email_is_unique(self) -> None:
        a = SchoolApplicationBuilder().as_payload()["applicant_email"]
        b = SchoolApplicationBuilder().as_payload()["applicant_email"]
        assert a != b


class TestIdentifierMatchers:
    def test_is_uuid_true_false(self) -> None:
        assert is_uuid(uuid.uuid4())
        assert is_uuid(str(uuid.uuid4()))
        assert not is_uuid("not-a-uuid")
        assert not is_uuid(123)

    def test_assert_uuid_returns_uuid(self) -> None:
        u = uuid.uuid4()
        assert assert_uuid(str(u)) == u

    def test_assert_uuid_raises(self) -> None:
        with pytest.raises(AssertionError):
            assert_uuid("nope")


class TestEnvelopeMatchers:
    def test_success_envelope(self) -> None:
        assert assert_success_envelope({"data": {"x": 1}, "meta": {}}) == {"x": 1}

    def test_success_envelope_missing_data_raises(self) -> None:
        with pytest.raises(AssertionError):
            assert_success_envelope({"meta": {}})

    def test_list_envelope(self) -> None:
        payload = {"data": [1, 2], "meta": {"next_cursor": None, "has_more": False}}
        assert assert_list_envelope(payload, min_items=2) == [1, 2]

    def test_error_envelope_with_code(self) -> None:
        payload = {
            "error": {"code": "ERR-APP-404", "message": "x", "category": "resource"}
        }
        err = assert_error_envelope(payload, code="ERR-APP-404", category="resource")
        assert err["message"] == "x"

    def test_error_envelope_wrong_code_raises(self) -> None:
        with pytest.raises(AssertionError):
            assert_error_envelope({"error": {"code": "A", "message": "m"}}, code="B")


class TestActivationUrlMatcher:
    def test_extracts_token(self) -> None:
        url = "http://localhost:5173/activate?token=abc123"
        assert assert_activation_url(url) == "abc123"

    def test_token_match(self) -> None:
        url = "http://localhost:5173/activate?token=xyz"
        assert assert_activation_url(url, token="xyz") == "xyz"

    def test_bad_url_raises(self) -> None:
        with pytest.raises(AssertionError):
            assert_activation_url("http://localhost/login")
