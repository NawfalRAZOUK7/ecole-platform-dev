/// Auth repository implementation — data layer.
///
/// Reference: S-092, S-093 — Secure token storage + auth flow
/// Login stores refresh token in secure storage.
/// Access token kept in memory (ApiClient).

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/domain/entities/user.dart';
import 'package:ecole_platform/domain/repositories/auth_repository.dart';
import 'package:ecole_platform/shared/secure_storage.dart';

class AuthRepositoryImpl implements AuthRepository {
  final ApiClient _api;
  final SecureTokenStorage _tokenStorage;

  AuthRepositoryImpl({
    required ApiClient api,
    required SecureTokenStorage tokenStorage,
  })  : _api = api,
        _tokenStorage = tokenStorage;

  @override
  Future<String> login(String email, String password, String schoolId) async {
    final resp = await _api.post(
      '/auth/login',
      body: {
        'email': email,
        'password': password,
        'school_id': schoolId,
      },
      skipAuth: true,
    );

    final accessToken = resp.data['access_token'] as String;
    _api.setAccessToken(accessToken);

    // Store refresh token if returned
    final refreshToken = resp.data['refresh_token'] as String?;
    if (refreshToken != null) {
      await _tokenStorage.saveRefreshToken(refreshToken);
    }

    return accessToken;
  }

  @override
  Future<String?> refreshToken() async {
    final token = await _api.accessToken != null
        ? _api.accessToken
        : null;
    return token;
  }

  @override
  Future<void> logout() async {
    try {
      await _api.post('/auth/logout');
    } catch (_) {
      // Ignore logout errors — always clear local state
    } finally {
      _api.setAccessToken(null);
      await _tokenStorage.clearAll();
    }
  }

  @override
  Future<User> getMe() async {
    final resp = await _api.get('/auth/me');
    return userFromJson(resp.data);
  }
}
