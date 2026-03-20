/// Auth repository interface — domain layer contract for authentication.
///
/// Reference: DEC-E2-001 — Data layer MUST NOT contain UI logic.
/// Phase 5A: Added 2FA verify, device info on login.
import '../entities/user.dart';

/// Login result — either a token or a 2FA challenge.
class LoginResult {
  final String? accessToken;
  final bool requires2fa;
  final String? tempToken;

  const LoginResult({
    this.accessToken,
    this.requires2fa = false,
    this.tempToken,
  });
}

/// 2FA setup response from POST /auth/2fa/setup.
class TwoFactorSetupData {
  final String provisioningUri;
  final String secret;

  const TwoFactorSetupData({
    required this.provisioningUri,
    required this.secret,
  });
}

/// 2FA verify-setup response with backup codes.
class TwoFactorVerifyResult {
  final List<String> backupCodes;
  final String message;

  const TwoFactorVerifyResult({
    required this.backupCodes,
    required this.message,
  });
}

abstract class AuthRepository {
  /// Login with email, password, and school ID.
  /// Returns [LoginResult] which may require 2FA verification.
  Future<LoginResult> login(
    String email,
    String password,
    String schoolId, {
    String? deviceName,
    String? userAgent,
  });

  /// Verify 2FA code during login flow.
  /// Returns access token on success.
  Future<String> verify2fa(String tempToken, String code);

  /// Refresh the access token using the stored refresh token.
  Future<String?> refreshToken();

  /// Logout — revoke session, clear tokens.
  Future<void> logout();

  /// Fetch current user profile.
  Future<User> getMe();

  /// Start 2FA setup — returns provisioning URI + secret.
  Future<TwoFactorSetupData> setup2fa();

  /// Verify 2FA setup with code — returns backup codes.
  Future<TwoFactorVerifyResult> verifySetup2fa(String code);

  /// Disable 2FA with a code.
  Future<void> disable2fa(String code);

  /// Change password.
  Future<void> changePassword(String currentPassword, String newPassword);
}
