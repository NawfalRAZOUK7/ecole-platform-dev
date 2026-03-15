/// Secure token storage using platform keychain/keystore.
///
/// Reference: DEC-E2-030 — Secure token/secrets storage
/// - Access token in memory only (held by ApiClient)
/// - Refresh token in native secure storage (Android Keystore / iOS Keychain)
/// - No PII or tokens in plain text logs

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

const String _refreshTokenKey = 'ecole_refresh_token';
const String _csrfTokenKey = 'ecole_csrf_token';

class SecureTokenStorage {
  final FlutterSecureStorage _storage;

  SecureTokenStorage()
      : _storage = const FlutterSecureStorage(
          aOptions: AndroidOptions(encryptedSharedPreferences: true),
          iOptions: IOSOptions(
            accessibility: KeychainAccessibility.first_unlock_this_device,
          ),
        );

  /// Save the refresh token to secure storage.
  Future<void> saveRefreshToken(String token) async {
    await _storage.write(key: _refreshTokenKey, value: token);
  }

  /// Retrieve the refresh token from secure storage.
  Future<String?> getRefreshToken() async {
    return _storage.read(key: _refreshTokenKey);
  }

  /// Save the CSRF token to secure storage.
  Future<void> saveCsrfToken(String token) async {
    await _storage.write(key: _csrfTokenKey, value: token);
  }

  /// Retrieve the CSRF token from secure storage.
  Future<String?> getCsrfToken() async {
    return _storage.read(key: _csrfTokenKey);
  }

  /// Clear all stored tokens (logout).
  Future<void> clearAll() async {
    await _storage.delete(key: _refreshTokenKey);
    await _storage.delete(key: _csrfTokenKey);
  }
}
