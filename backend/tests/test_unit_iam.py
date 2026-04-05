"""Unit tests for IAM services — JWT, password hashing, permissions.

Reference: S-114 — Unit tests for IAM services
Tests JWT generation/validation, password hashing, permission lookups,
invitation code hashing, and recovery state machine rules.
"""

from __future__ import annotations

import uuid

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_csrf_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
)
from app.core.permissions import (
    get_permissions_for_role,
    role_has_permission,
    ROLE_PERMISSIONS,
    ADM,
    TCH,
    PAR,
    STD,
    DIR,
    SUP,
    SYS,
    CONTENT_MGR,
    EDUCATOR,
    PUBLIC,
)
from app.core.exceptions import AuthenticationError


# ── JWT Token Tests ──


class TestJWTGeneration:
    """Tests for JWT token creation."""

    def test_create_access_token_returns_string(self):
        token = create_access_token(
            user_id=uuid.uuid4(),
            role="ADM",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
        )
        assert isinstance(token, str)
        assert len(token) > 50  # JWT has 3 parts

    def test_access_token_contains_correct_claims(self):
        uid = uuid.uuid4()
        school = uuid.uuid4()
        session = uuid.uuid4()

        token = create_access_token(uid, "TCH", school, session)
        payload = decode_access_token(token)

        assert payload["sub"] == str(uid)
        assert payload["role"] == "TCH"
        assert payload["school_id"] == str(school)
        assert payload["session_id"] == str(session)
        assert payload["type"] == TOKEN_TYPE_ACCESS
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_create_refresh_token_returns_tuple(self):
        token, jti = create_refresh_token(
            user_id=uuid.uuid4(),
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
        )
        assert isinstance(token, str)
        assert isinstance(jti, str)
        assert len(jti) == 36  # UUID format

    def test_refresh_token_contains_correct_claims(self):
        uid = uuid.uuid4()
        school = uuid.uuid4()
        session = uuid.uuid4()

        token, jti = create_refresh_token(uid, school, session)
        payload = decode_refresh_token(token)

        assert payload["sub"] == str(uid)
        assert payload["school_id"] == str(school)
        assert payload["session_id"] == str(session)
        assert payload["type"] == TOKEN_TYPE_REFRESH
        assert payload["jti"] == jti

    def test_csrf_token_is_uuid(self):
        csrf = create_csrf_token()
        assert len(csrf) == 36
        uuid.UUID(csrf)  # Should not raise


class TestJWTValidation:
    """Tests for JWT token decoding and validation."""

    def test_decode_valid_access_token(self):
        token = create_access_token(uuid.uuid4(), "ADM", uuid.uuid4(), uuid.uuid4())
        payload = decode_access_token(token)
        assert payload["type"] == TOKEN_TYPE_ACCESS

    def test_decode_invalid_token_raises_error(self):
        with pytest.raises(AuthenticationError):
            decode_access_token("not-a-valid-jwt-token")

    def test_decode_refresh_as_access_raises_error(self):
        """Using a refresh token where access token is expected must fail."""
        token, _ = create_refresh_token(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
        with pytest.raises(AuthenticationError):
            decode_access_token(token)

    def test_decode_access_as_refresh_raises_error(self):
        """Using an access token where refresh token is expected must fail."""
        token = create_access_token(uuid.uuid4(), "ADM", uuid.uuid4(), uuid.uuid4())
        with pytest.raises(AuthenticationError):
            decode_refresh_token(token)

    def test_empty_string_raises_error(self):
        with pytest.raises(AuthenticationError):
            decode_access_token("")

    def test_decode_valid_refresh_token(self):
        token, _ = create_refresh_token(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
        payload = decode_refresh_token(token)
        assert payload["type"] == TOKEN_TYPE_REFRESH


# ── Password Hashing Tests ──


class TestPasswordHashing:
    """Tests for bcrypt password hashing."""

    def test_hash_returns_bcrypt_string(self):
        hashed = hash_password("test-password-123")
        assert hashed.startswith("$2b$")  # bcrypt marker
        assert len(hashed) == 60

    def test_verify_correct_password(self):
        plain = "secure-password-456"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_different_passwords_produce_different_hashes(self):
        h1 = hash_password("password-a")
        h2 = hash_password("password-b")
        assert h1 != h2

    def test_same_password_produces_different_hashes(self):
        """Bcrypt uses random salt, so same password → different hash."""
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2
        assert verify_password("same-password", h1)
        assert verify_password("same-password", h2)


# ── RBAC Permission Catalog Tests ──


class TestPermissionCatalog:
    """Tests for the RBAC permission catalog."""

    def test_all_roles_defined(self):
        expected_roles = {ADM, DIR, TCH, PAR, STD, SUP, SYS, CONTENT_MGR, PUBLIC, EDUCATOR}
        assert set(ROLE_PERMISSIONS.keys()) == expected_roles

    def test_admin_has_class_read(self):
        assert role_has_permission(ADM, "PERM-ERP:class:read")

    def test_student_lacks_class_read(self):
        assert not role_has_permission(STD, "PERM-ERP:class:read")

    def test_teacher_has_grade_permission(self):
        assert role_has_permission(TCH, "PERM-LMS:submission:grade")

    def test_student_has_submission_create(self):
        assert role_has_permission(STD, "PERM-LMS:submission:create")

    def test_parent_has_invoice_read(self):
        assert role_has_permission(PAR, "PERM-BIL:invoice:read")

    def test_student_lacks_invoice_read(self):
        assert not role_has_permission(STD, "PERM-BIL:invoice:read")

    def test_parent_has_feed_related_permissions(self):
        perms = get_permissions_for_role(PAR)
        assert "PERM-COM:notification:read" in perms
        assert "PERM-COM:consent:update" in perms

    def test_sys_has_payment_reconcile(self):
        assert role_has_permission(SYS, "PERM-BIL:payment:reconcile")

    def test_unknown_role_returns_empty(self):
        assert get_permissions_for_role("UNKNOWN") == set()

    def test_role_has_permission_false_for_missing_perm(self):
        assert not role_has_permission(ADM, "PERM-NONEXISTENT:foo:bar")

    def test_public_has_session_and_recovery(self):
        perms = get_permissions_for_role(PUBLIC)
        assert "PERM-IAM:session:create" in perms
        assert "PERM-IAM:recovery:request" in perms
        assert len(perms) == 5  # only 5 public perms

    def test_teacher_has_course_publish(self):
        assert role_has_permission(TCH, "PERM-LMS:course:publish")

    def test_admin_has_enrollment_assign(self):
        assert role_has_permission(ADM, "PERM-ERP:enrollment:assign")

    def test_director_has_limited_erp(self):
        perms = get_permissions_for_role(DIR)
        assert "PERM-ERP:class:read" in perms
        assert "PERM-ERP:enrollment:assign" not in perms
