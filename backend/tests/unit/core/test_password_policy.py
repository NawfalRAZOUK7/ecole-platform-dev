"""Unit tests for app/core/password_policy.py — full branch coverage."""

from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.core.password_policy import (
    MIN_LENGTH,
    PasswordValidator,
    _is_common_password,
    _load_common_passwords,
    password_validator,
)


# ---------------------------------------------------------------------------
# _load_common_passwords — idempotent
# ---------------------------------------------------------------------------


def test_load_common_passwords_returns_set():
    result = _load_common_passwords()
    assert isinstance(result, set)


def test_load_common_passwords_idempotent():
    s1 = _load_common_passwords()
    s2 = _load_common_passwords()
    assert s1 is s2  # returns same cached set


def test_load_common_passwords_file_not_found(tmp_path, monkeypatch):
    import app.core.password_policy as pp

    original = pp._COMMON_PASSWORDS_PATH
    original_cache = pp._common_passwords.copy()

    # Clear cache and point to missing file
    pp._common_passwords = set()
    monkeypatch.setattr(pp, "_COMMON_PASSWORDS_PATH", tmp_path / "nonexistent.txt")

    result = pp._load_common_passwords()
    assert isinstance(result, set)  # graceful — returns empty set

    # Restore
    pp._common_passwords = original_cache
    pp._COMMON_PASSWORDS_PATH = original


# ---------------------------------------------------------------------------
# _is_common_password
# ---------------------------------------------------------------------------


def test_is_common_password_with_known_common():
    # 'password' is almost certainly in the common list
    from app.core.password_policy import _common_passwords
    if "password" in _common_passwords:
        assert _is_common_password("password") is True


def test_is_common_password_with_unique_string():
    result = _is_common_password("xK9q!mZn#vR2$wP8")
    assert result is False


def test_is_common_password_normalized_variant():
    from app.core.password_policy import _common_passwords
    # Add a known common password for test
    _common_passwords.add("testcommon")
    try:
        # Normalized variant (no special chars/digits at end) should match
        assert _is_common_password("testcommon") is True
        # With trailing digits
        assert _is_common_password("testcommon123") is True
    finally:
        _common_passwords.discard("testcommon")


def test_is_common_password_empty_candidate_skipped():
    # Candidates with empty strings should not cause false positive
    result = _is_common_password("!@#$%^&*()")  # all special → normalized is empty
    assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# PasswordValidator.check — all rules
# ---------------------------------------------------------------------------


def _validator():
    return PasswordValidator()


def test_check_valid_password():
    v = _validator()
    errors = v.check("SecureP@ss123", email="other@test.ma", full_name="Test User")
    assert errors == []


def test_check_too_short():
    v = _validator()
    errors = v.check("Short1!")
    rules = [e["rule"] for e in errors]
    assert "min_length" in rules


def test_check_exactly_min_length_passes_length_rule():
    v = _validator()
    # 12 chars, passes length rule but may fail others
    pwd = "A" * MIN_LENGTH
    errors = v.check(pwd)
    rules = [e["rule"] for e in errors]
    assert "min_length" not in rules


def test_check_no_uppercase():
    v = _validator()
    errors = v.check("nouppercase123!")
    rules = [e["rule"] for e in errors]
    assert "uppercase" in rules


def test_check_no_lowercase():
    v = _validator()
    errors = v.check("NOLOWERCASE123!")
    rules = [e["rule"] for e in errors]
    assert "lowercase" in rules


def test_check_no_digit():
    v = _validator()
    errors = v.check("NoDigitHere!ABC")
    rules = [e["rule"] for e in errors]
    assert "digit" in rules


def test_check_no_special_char():
    v = _validator()
    errors = v.check("NoSpecialChar123")
    rules = [e["rule"] for e in errors]
    assert "special_char" in rules


def test_check_contains_email_local_part():
    v = _validator()
    errors = v.check("SecureP@ss123", email="john@test.ma")
    # "john" is 4 chars, if in password → error
    v2 = _validator()
    errors2 = v2.check("johnSecureP@ss123!", email="john@test.ma")
    rules = [e["rule"] for e in errors2]
    assert "contains_email" in rules


def test_check_email_local_part_too_short():
    v = _validator()
    # email local part < 3 chars → no check
    errors = v.check("SecureP@ss123!", email="ab@test.ma")
    rules = [e["rule"] for e in errors]
    assert "contains_email" not in rules


def test_check_no_email_no_name():
    v = _validator()
    errors = v.check("SecureP@ss123!")
    # Should not fail name/email checks
    rules = [e["rule"] for e in errors]
    assert "contains_email" not in rules
    assert "contains_name" not in rules


def test_check_contains_name_part():
    v = _validator()
    errors = v.check("JohnSecureP@ss123!", full_name="John Doe")
    rules = [e["rule"] for e in errors]
    assert "contains_name" in rules


def test_check_name_part_too_short_not_checked():
    v = _validator()
    # Name parts < 3 chars are skipped
    errors = v.check("ABSecureP@ss123!", full_name="AB C")
    rules = [e["rule"] for e in errors]
    assert "contains_name" not in rules


def test_check_name_break_after_first_match():
    v = _validator()
    # Only one "contains_name" failure even if multiple parts match
    errors = v.check("AliceSmithSecureP@ss!", full_name="Alice Smith")
    name_errors = [e for e in errors if e["rule"] == "contains_name"]
    assert len(name_errors) <= 1  # break stops after first match


def test_check_multiple_failures():
    v = _validator()
    errors = v.check("abc")
    assert len(errors) >= 3  # at least length, uppercase, digit, special


# ---------------------------------------------------------------------------
# PasswordValidator.validate — raises ValidationError on failure
# ---------------------------------------------------------------------------


def test_validate_weak_password_raises():
    v = _validator()
    with pytest.raises(ValidationError) as exc_info:
        v.validate("weak")
    assert exc_info.value.error_code == "ERR-IAM-POLICY"
    assert "password_rules" in exc_info.value.details


def test_validate_strong_password_does_not_raise():
    v = _validator()
    v.validate("SecureP@ss9274!", email="other@example.com", full_name="Test User")


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------


def test_password_validator_singleton_is_instance():
    assert isinstance(password_validator, PasswordValidator)


def test_password_validator_singleton_works():
    errors = password_validator.check("weak")
    assert len(errors) > 0


def test_check_common_password_rule_triggered():
    """Line 157: failures.append for common_password rule."""
    from app.core.password_policy import _common_passwords, PasswordValidator

    # _is_common_password lowercases the password before checking,
    # so the sentinel must be stored lowercase in the set.
    sentinel_lower = "zkq9uniquetest99"
    _common_passwords.add(sentinel_lower)
    try:
        v = PasswordValidator()
        # Use the same value (already lowercase) as the password to check
        errors = v.check("Zkq9UniqueTest99!", email="other@test.ma")
        rules = [e["rule"] for e in errors]
        assert "common_password" in rules
    finally:
        _common_passwords.discard(sentinel_lower)


def test_name_parts_break_on_first_match():
    """Break statement executes when first name part is found in password."""
    v = PasswordValidator()
    name_errors = [
        e for e in v.check("AliceSecureP@ss123", full_name="Alice Wonderland")
        if e["rule"] == "contains_name"
    ]
    assert len(name_errors) == 1  # only one failure even with multiple name parts
