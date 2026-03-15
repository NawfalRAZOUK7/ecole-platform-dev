/// Auth repository interface — domain layer contract for authentication.
///
/// Reference: DEC-E2-001 — Data layer MUST NOT contain UI logic.
import '../entities/user.dart';

abstract class AuthRepository {
  /// Login with email, password, and school ID.
  /// Returns access token on success.
  Future<String> login(String email, String password, String schoolId);

  /// Refresh the access token using the stored refresh token.
  /// Returns new access token or null if refresh fails.
  Future<String?> refreshToken();

  /// Logout — revoke session, clear tokens.
  Future<void> logout();

  /// Fetch current user profile.
  Future<User> getMe();
}
