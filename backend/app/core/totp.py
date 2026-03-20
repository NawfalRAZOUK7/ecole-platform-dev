"""TOTP two-factor authentication utilities.

Reference: Phase 2B — Two-Factor Authentication (TOTP) & Email Verification
- TOTP secret generation (base32, 32 bytes)
- QR code provisioning URI (otpauth:// format)
- Code verification with 1-step drift tolerance (30s window)
- Backup code generation (10 codes, 8 chars each, bcrypt hashed)
"""

from __future__ import annotations

import secrets
import string

import bcrypt
import pyotp


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TOTP_ISSUER = "ÉcolePlatform"
TOTP_DIGITS = 6
TOTP_INTERVAL = 30  # seconds
TOTP_VALID_WINDOW = 1  # accept codes ±1 step (drift tolerance)
BACKUP_CODE_COUNT = 10
BACKUP_CODE_LENGTH = 8


# ---------------------------------------------------------------------------
# TOTP secret & QR URI
# ---------------------------------------------------------------------------
def generate_totp_secret() -> str:
    """Generate a new TOTP secret (base32, 32 bytes).

    Returns the base32-encoded secret string that should be stored (encrypted)
    in the user's totp_secret column.
    """
    return pyotp.random_base32(length=32)


def get_provisioning_uri(
    secret: str,
    email: str,
    issuer: str | None = None,
) -> str:
    """Generate an otpauth:// URI for QR code provisioning.

    This URI is encoded into a QR code that authenticator apps scan.
    Format: otpauth://totp/{issuer}:{email}?secret={secret}&issuer={issuer}&digits=6&period=30
    """
    totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
    return totp.provisioning_uri(
        name=email,
        issuer_name=issuer or TOTP_ISSUER,
    )


# ---------------------------------------------------------------------------
# TOTP verification
# ---------------------------------------------------------------------------
def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a TOTP code against the secret.

    Accepts codes within ±1 time step (TOTP_VALID_WINDOW) to account for
    clock drift between the server and the authenticator app.
    """
    totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
    return totp.verify(code, valid_window=TOTP_VALID_WINDOW)


# ---------------------------------------------------------------------------
# Backup codes
# ---------------------------------------------------------------------------
def generate_backup_codes() -> list[str]:
    """Generate a set of plaintext backup codes.

    Returns BACKUP_CODE_COUNT codes, each BACKUP_CODE_LENGTH chars long,
    alphanumeric uppercase. These are shown to the user once and must be
    stored bcrypt-hashed.
    """
    alphabet = string.ascii_uppercase + string.digits
    codes = []
    for _ in range(BACKUP_CODE_COUNT):
        code = "".join(secrets.choice(alphabet) for _ in range(BACKUP_CODE_LENGTH))
        codes.append(code)
    return codes


def hash_backup_codes(codes: list[str]) -> list[str]:
    """Hash backup codes with bcrypt for storage.

    Returns a list of bcrypt hash strings (one per code).
    """
    hashed = []
    for code in codes:
        salt = bcrypt.gensalt(rounds=10)
        h = bcrypt.hashpw(code.encode("utf-8"), salt).decode("utf-8")
        hashed.append(h)
    return hashed


def verify_backup_code(code: str, hashed_codes: list[str]) -> int | None:
    """Verify a backup code against the list of hashed codes.

    Returns the index of the matching code (for consumption) or None if no match.
    Codes are single-use: the caller must remove the consumed code from the list.
    """
    for i, h in enumerate(hashed_codes):
        if bcrypt.checkpw(code.encode("utf-8"), h.encode("utf-8")):
            return i
    return None
