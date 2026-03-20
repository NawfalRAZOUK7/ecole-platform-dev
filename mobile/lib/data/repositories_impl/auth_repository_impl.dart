/// Auth repository implementation — data layer.
///
/// Reference: S-092, S-093 — Secure token storage + auth flow
/// Phase 5A: 2FA verify, device info on login, 2FA setup/disable, change password.

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
  Future<LoginResult> login(
    String email,
    String password,
    String schoolId, {
    String? deviceName,
    String? userAgent,
  }) async {
    final body = <String, dynamic>{
      'email': email,
      'password': password,
      'school_id': schoolId,
    };
    if (deviceName != null) body['device_name'] = deviceName;
    if (userAgent != null) body['user_agent'] = userAgent;

    final resp = await _api.post(
      '/auth/login',
      body: body,
      skipAuth: true,
    );

    // Check if 2FA is required
    if (resp.data['requires_2fa'] == true) {
      return LoginResult(
        requires2fa: true,
        tempToken: resp.data['temp_token'] as String?,
      );
    }

    final accessToken = resp.data['access_token'] as String;
    _api.setAccessToken(accessToken);

    // Store refresh token if returned
    final refreshToken = resp.data['refresh_token'] as String?;
    if (refreshToken != null) {
      await _tokenStorage.saveRefreshToken(refreshToken);
    }

    return LoginResult(accessToken: accessToken);
  }

  @override
  Future<String> verify2fa(String tempToken, String code) async {
    final resp = await _api.post(
      '/auth/2fa/verify',
      body: {
        'temp_token': tempToken,
        'code': code,
      },
      skipAuth: true,
    );

    final accessToken = resp.data['access_token'] as String;
    _api.setAccessToken(accessToken);

    final refreshToken = resp.data['refresh_token'] as String?;
    if (refreshToken != null) {
      await _tokenStorage.saveRefreshToken(refreshToken);
    }

    return accessToken;
  }

  @override
  Future<String?> refreshToken() async {
    final token =
        _api.accessToken != null ? _api.accessToken : null;
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

  @override
  Future<TwoFactorSetupData> setup2fa() async {
    final resp = await _api.post('/auth/2fa/setup');
    return TwoFactorSetupData(
      provisioningUri: resp.data['provisioning_uri'] as String,
      secret: resp.data['secret'] as String,
    );
  }

  @override
  Future<TwoFactorVerifyResult> verifySetup2fa(String code) async {
    final resp = await _api.post(
      '/auth/2fa/verify-setup',
      body: {'code': code},
    );
    final codes = (resp.data['backup_codes'] as List<dynamic>).cast<String>();
    return TwoFactorVerifyResult(
      backupCodes: codes,
      message: resp.data['message'] as String? ?? 'OK',
    );
  }

  @override
  Future<void> disable2fa(String code) async {
    await _api.post('/auth/2fa/disable', body: {'code': code});
  }

  @override
  Future<void> changePassword(
      String currentPassword, String newPassword) async {
    await _api.post('/auth/change-password', body: {
      'current_password': currentPassword,
      'new_password': newPassword,
    });
  }
}
