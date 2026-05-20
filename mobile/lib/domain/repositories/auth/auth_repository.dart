/// Auth repository interface — domain layer contract for authentication.
///
/// Reference: DEC-E2-001 — Data layer MUST NOT contain UI logic.
/// Phase 5A: Added 2FA verify, device info on login.
import 'package:ecole_platform/domain/entities/user/child_link.dart';
import 'package:ecole_platform/domain/entities/user/user.dart';

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

/// Registration result — token + user info for immediate login.
class RegisterResult {
  final String accessToken;
  final String userId;
  final String schoolId;
  final String role;
  final bool emailVerificationRequired;

  const RegisterResult({
    required this.accessToken,
    required this.userId,
    required this.schoolId,
    required this.role,
    required this.emailVerificationRequired,
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

  /// Register with invitation code.
  Future<RegisterResult> register({
    required String code,
    required String email,
    required String fullName,
    String? phone,
    required String password,
    Map<String, String> profileData,
  });

  /// Verify email OTP after registration.
  Future<void> verifyEmail({
    required String userId,
    required String schoolId,
    required String otp,
  });

  /// Verify 2FA code during login flow.
  /// Returns access token on success.
  Future<String> verify2fa(String tempToken, String code);

  /// Refresh the access token using the stored refresh token.
  Future<String?> refreshToken();

  Future<void> requestRecovery(String email);

  Future<bool> verifyRecovery(String token, String code);

  Future<void> resetPassword(String token, String newPassword);

  /// Logout — revoke session, clear tokens.
  Future<void> logout();

  /// Fetch current user profile.
  Future<User> getMe();

  /// Fetch role-specific profile data.
  Future<Map<String, dynamic>> getProfile();

  /// Update role-specific profile data.
  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> data);

  /// Start 2FA setup — returns provisioning URI + secret.
  Future<TwoFactorSetupData> setup2fa();

  /// Verify 2FA setup with code — returns backup codes.
  Future<TwoFactorVerifyResult> verifySetup2fa(String code);

  /// Disable 2FA with a code.
  Future<void> disable2fa(String code);

  /// Change password.
  Future<void> changePassword(String currentPassword, String newPassword);

  /// Fetch linked children (PAR role only).
  Future<List<ChildLink>> getChildren();

  /// Get OAuth authorization URL from backend.
  Future<Map<String, String>> getOAuthUrl(String provider, String redirectUri);

  /// Exchange OAuth code for tokens.
  Future<LoginResult> oauthLogin(
    String provider,
    String code,
    String redirectUri,
    String schoolId,
  );
}
