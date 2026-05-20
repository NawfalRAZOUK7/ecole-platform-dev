"""WebAuthn/Passkeys service for passwordless authentication.

Reference: Phase 10 — WebAuthn/Passkeys Support
"""

import json
from typing import Optional

from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import (
    bytes_to_base64url,
    base64url_to_bytes,
)
from webauthn.helpers.structs import (
    AuthenticationCredential,
    RegistrationCredential,
)

from app.core.config import settings


class WebAuthnService:
    """Service for WebAuthn/Passkeys operations."""

    def __init__(self):
        self.rp_id = getattr(settings, "webauthn_rp_id", "localhost")
        self.rp_name = getattr(settings, "webauthn_rp_name", "École Platform")
        self.origin = getattr(settings, "webauthn_origin", "http://localhost:8000")

    def generate_registration_options(
        self,
        user_id: str,
        username: str,
        display_name: str,
        exclude_credentials: Optional[list[str]] = None,
    ) -> dict:
        """Generate WebAuthn registration options for a new passkey."""
        options = generate_registration_options(
            rp_id=self.rp_id,
            rp_name=self.rp_name,
            user_id=user_id.encode(),
            user_name=username,
            display_name=display_name,
            exclude_credentials=exclude_credentials or [],
            authenticator_selection={
                "authenticator_attachment": "platform",
                "user_verification": "preferred",
            },
            attestation="none",
        )
        return json.loads(options_to_json(options))

    def verify_registration_response(
        self,
        registration_response: dict,
        expected_challenge: str,
        expected_origin: Optional[str] = None,
    ) -> dict:
        """Verify WebAuthn registration response."""
        if expected_origin is None:
            expected_origin = self.origin

        credential = RegistrationCredential(
            id=base64url_to_bytes(registration_response["id"]),
            raw_id=base64url_to_bytes(registration_response["id"]),
            response=registration_response["response"],
            authenticator_data=base64url_to_bytes(
                registration_response["response"]["authenticatorData"]
            ),
            client_data_json=base64url_to_bytes(
                registration_response["response"]["clientDataJSON"]
            ),
            attestation_object=base64url_to_bytes(
                registration_response["response"]["attestationObject"]
            ),
        )

        verification = verify_registration_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(expected_challenge),
            expected_rp_id=self.rp_id,
            expected_origin=expected_origin,
        )

        return {
            "credential_id": bytes_to_base64url(verification.credential_id),
            "public_key": bytes_to_base64url(verification.public_key),
            "sign_count": verification.sign_count,
            "aaguid": bytes_to_base64url(verification.aaguid)
            if verification.aaguid
            else None,
        }

    def generate_authentication_options(
        self,
        allow_credentials: Optional[list[str]] = None,
        user_verification: str = "preferred",
    ) -> dict:
        """Generate WebAuthn authentication options for login."""
        options = generate_authentication_options(
            rp_id=self.rp_id,
            allow_credentials=allow_credentials or [],
            user_verification=user_verification,
        )
        return json.loads(options_to_json(options))

    def verify_authentication_response(
        self,
        authentication_response: dict,
        expected_challenge: str,
        public_key: str,
        current_sign_count: int,
        expected_origin: Optional[str] = None,
    ) -> dict:
        """Verify WebAuthn authentication response."""
        if expected_origin is None:
            expected_origin = self.origin

        credential = AuthenticationCredential(
            id=base64url_to_bytes(authentication_response["id"]),
            raw_id=base64url_to_bytes(authentication_response["id"]),
            response=authentication_response["response"],
            authenticator_data=base64url_to_bytes(
                authentication_response["response"]["authenticatorData"]
            ),
            client_data_json=base64url_to_bytes(
                authentication_response["response"]["clientDataJSON"]
            ),
            signature=base64url_to_bytes(
                authentication_response["response"]["signature"]
            ),
            user_handle=base64url_to_bytes(
                authentication_response["response"].get("userHandle", "")
            ),
        )

        verification = verify_authentication_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(expected_challenge),
            expected_rp_id=self.rp_id,
            expected_origin=expected_origin,
            credential_public_key=base64url_to_bytes(public_key),
            credential_current_sign_count=current_sign_count,
        )

        return {
            "credential_id": bytes_to_base64url(verification.credential_id),
            "new_sign_count": verification.new_sign_count,
            "verified": verification.verified,
        }
