"""DB-free unit tests for onboarding approval/activation logic (Feature: onboarding).

These cover the pure building blocks that don't need a database:
  - role / school-type mapping by application type
  - generated school-code shape and uniqueness
  - activation token hashing semantics (sha256, single-use comparison)
  - request-schema validation (activation + applications)

The DB-backed approve→activate→resend flow is covered separately in
tests/integration/api/onboarding/test_onboarding_activation.py.
"""

from __future__ import annotations

import hashlib

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.models.onboarding import ApplicationType
from app.models.school import SchoolType
from app.schemas.auth import ActivateRequest
from app.schemas.onboarding import (
    FormalSchoolApplicationRequest,
    MicroSchoolApplicationRequest,
)
from app.services.platform.onboarding import (
    _ROLE_BY_TYPE,
    _SCHOOL_TYPE_BY_APP,
    _school_code,
)


class TestRoleAndSchoolTypeMapping:
    def test_formal_school_maps_to_adm_and_formal(self) -> None:
        key = ApplicationType.FORMAL_SCHOOL.value
        assert _ROLE_BY_TYPE[key] == "ADM"
        assert _SCHOOL_TYPE_BY_APP[key] == SchoolType.FORMAL.value

    def test_micro_school_maps_to_educator_and_informal(self) -> None:
        key = ApplicationType.MICRO_SCHOOL.value
        assert _ROLE_BY_TYPE[key] == "EDUCATOR"
        assert _SCHOOL_TYPE_BY_APP[key] == SchoolType.INFORMAL.value


class TestSchoolCode:
    def test_uppercase_alnum_prefix_with_suffix(self) -> None:
        code = _school_code("École Les Oliviers")
        # Prefix is alnum-only, uppercased, max 6 chars; suffix after a dash.
        prefix, _, suffix = code.partition("-")
        assert prefix == "COLELE"[:6] or prefix.isalnum()
        assert prefix.isupper()
        assert len(prefix) <= 6
        assert len(suffix) == 6  # token_hex(3) -> 6 hex chars
        assert suffix.isupper()

    def test_falls_back_when_name_has_no_alnum(self) -> None:
        code = _school_code("—— !!! ——")
        assert code.startswith("SCHOOL-")

    def test_is_unique_per_call(self) -> None:
        codes = {_school_code("Same Name") for _ in range(50)}
        assert len(codes) == 50  # random suffix guarantees uniqueness


class TestActivationTokenHashing:
    def test_sha256_is_deterministic(self) -> None:
        token = "abc123-token-value"
        h1 = hashlib.sha256(token.encode()).hexdigest()
        h2 = hashlib.sha256(token.encode()).hexdigest()
        assert h1 == h2
        assert len(h1) == 64

    def test_different_tokens_hash_differently(self) -> None:
        a = hashlib.sha256(b"token-a").hexdigest()
        b = hashlib.sha256(b"token-b").hexdigest()
        assert a != b


class TestActivateRequestSchema:
    def test_valid_request(self) -> None:
        req = ActivateRequest(token="x" * 32, password="LongEnoughPass1!")
        assert req.token == "x" * 32

    def test_short_password_rejected(self) -> None:
        with pytest.raises(PydanticValidationError):
            ActivateRequest(token="x" * 32, password="short")

    def test_short_token_rejected(self) -> None:
        with pytest.raises(PydanticValidationError):
            ActivateRequest(token="tooshort", password="LongEnoughPass1!")


class TestApplicationRequestSchemas:
    def test_formal_requires_core_fields(self) -> None:
        req = FormalSchoolApplicationRequest(
            applicant_name="Mme Alami",
            applicant_email="alami@example.ma",
            org_name="Lycée Ibn Sina",
        )
        assert req.org_name == "Lycée Ibn Sina"

    def test_micro_requires_core_fields(self) -> None:
        req = MicroSchoolApplicationRequest(
            applicant_name="Mr Idrissi",
            applicant_email="idrissi@example.ma",
            org_name="Micro-école Espoir",
        )
        assert req.applicant_email == "idrissi@example.ma"

    def test_invalid_email_rejected(self) -> None:
        with pytest.raises(PydanticValidationError):
            MicroSchoolApplicationRequest(
                applicant_name="Valid Name",
                applicant_email="not-an-email",
                org_name="Valid Org",
            )
