"""Password policy enforcement — strong password validation.

Reference: Phase 2A — Password Policy & Session Management
Rules:
  - Minimum 12 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
  - At least 1 special character
  - Not in common passwords list (data/common_passwords.txt)
  - Must not contain user's name or email local part
Returns structured errors listing all failed rules.
"""

from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import Any

from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load common passwords (one-time at module import)
# ---------------------------------------------------------------------------
_COMMON_PASSWORDS_PATH = Path(__file__).resolve().parent.parent / "data" / "common_passwords.txt"

_common_passwords: set[str] = set()


def _load_common_passwords() -> set[str]:
    """Load common passwords from file (lowercase, ignore comments/blanks)."""
    global _common_passwords
    if _common_passwords:
        return _common_passwords
    try:
        with open(_COMMON_PASSWORDS_PATH, encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if word and not word.startswith("#"):
                    _common_passwords.add(word.lower())
        logger.info("Loaded %d common passwords from %s", len(_common_passwords), _COMMON_PASSWORDS_PATH)
    except FileNotFoundError:
        logger.warning("Common passwords file not found: %s", _COMMON_PASSWORDS_PATH)
    return _common_passwords


# Pre-load on import
_load_common_passwords()

# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------
MIN_LENGTH = 12
SPECIAL_CHARS = r"""!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~"""


class PasswordValidator:
    """Validates passwords against the platform security policy.

    Usage:
        validator = PasswordValidator()
        validator.validate("weakpwd", email="user@example.com", full_name="John Doe")
        # Raises ValidationError with structured details of failed rules

        # Or check without raising:
        errors = validator.check("weakpwd", email="user@example.com")
        if errors:
            print(errors)  # list of dicts with rule + message
    """

    def check(
        self,
        password: str,
        *,
        email: str | None = None,
        full_name: str | None = None,
    ) -> list[dict[str, str]]:
        """Check password against all rules, returning list of failures.

        Each failure is a dict with 'rule' (machine-readable) and 'message' (human-readable).
        Returns empty list if password passes all checks.
        """
        failures: list[dict[str, str]] = []

        # Rule 1: minimum length
        if len(password) < MIN_LENGTH:
            failures.append({
                "rule": "min_length",
                "message": f"Password must be at least {MIN_LENGTH} characters long",
            })

        # Rule 2: uppercase
        if not re.search(r"[A-Z]", password):
            failures.append({
                "rule": "uppercase",
                "message": "Password must contain at least one uppercase letter",
            })

        # Rule 3: lowercase
        if not re.search(r"[a-z]", password):
            failures.append({
                "rule": "lowercase",
                "message": "Password must contain at least one lowercase letter",
            })

        # Rule 4: digit
        if not re.search(r"\d", password):
            failures.append({
                "rule": "digit",
                "message": "Password must contain at least one digit",
            })

        # Rule 5: special character
        if not re.search(r"[!@#$%^&*()\-_=+\[\]{};':\"\\|,.<>/?`~]", password):
            failures.append({
                "rule": "special_char",
                "message": "Password must contain at least one special character (!@#$%^&*...)",
            })

        # Rule 6: not a common password
        if password.lower() in _common_passwords:
            failures.append({
                "rule": "common_password",
                "message": "This password is too common and easily guessable",
            })

        # Rule 7: must not contain email local part
        if email:
            local_part = email.split("@")[0].lower()
            if len(local_part) >= 3 and local_part in password.lower():
                failures.append({
                    "rule": "contains_email",
                    "message": "Password must not contain your email address",
                })

        # Rule 8: must not contain parts of user's name
        if full_name:
            name_parts = [p.lower() for p in full_name.split() if len(p) >= 3]
            pwd_lower = password.lower()
            for part in name_parts:
                if part in pwd_lower:
                    failures.append({
                        "rule": "contains_name",
                        "message": "Password must not contain your name",
                    })
                    break  # One failure is enough

        return failures

    def validate(
        self,
        password: str,
        *,
        email: str | None = None,
        full_name: str | None = None,
    ) -> None:
        """Validate password, raising ValidationError if any rules fail.

        The error includes structured details with all failed rules.
        """
        failures = self.check(password, email=email, full_name=full_name)
        if failures:
            raise ValidationError(
                "Password does not meet security requirements",
                error_code="ERR-IAM-POLICY",
                details={"password_rules": failures},
            )


# Module-level singleton for convenience
password_validator = PasswordValidator()
