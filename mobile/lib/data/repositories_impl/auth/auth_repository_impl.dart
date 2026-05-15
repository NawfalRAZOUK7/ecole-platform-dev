/// Auth repository implementation — data layer.
///
/// Reference: S-092, S-093 — Secure token storage + auth flow
/// Phase 5A: 2FA verify, device info on login, 2FA setup/disable, change password.

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/domain/entities/user/child_link.dart';
import 'package:ecole_platform/domain/entities/user/user.dart';
import 'package:ecole_platform/domain/repositories/auth/auth_repository.dart';
import 'package:ecole_platform/core/storage/secure_storage.dart';

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
  Future<RegisterResult> register({
    required String code,
    required String email,
    required String fullName,
    String? phone,
    required String password,
    Map<String, String> profileData = const {},
  }) async {
    final body = <String, dynamic>{
      'code': code,
      'email': email,
      'full_name': fullName,
      'password': password,
      'profile_data': profileData,
    };
    if (phone != null && phone.isNotEmpty) body['phone'] = phone;

    final resp = await _api.post('/auth/register', body: body, skipAuth: true);

    final accessToken = resp.data['access_token'] as String;
    _api.setAccessToken(accessToken);

    final refreshToken = resp.data['refresh_token'] as String?;
    if (refreshToken != null) {
      await _tokenStorage.saveRefreshToken(refreshToken);
    }

    return RegisterResult(
      accessToken: accessToken,
      userId: resp.data['user_id'] as String,
      schoolId: resp.data['school_id'] as String,
      role: resp.data['role'] as String,
      emailVerificationRequired:
          resp.data['email_verification_required'] as bool? ?? false,
    );
  }

  @override
  Future<void> verifyEmail({
    required String userId,
    required String schoolId,
    required String otp,
  }) async {
    await _api.post(
      '/auth/verify-email',
      body: {
        'user_id': userId,
        'school_id': schoolId,
        'otp': otp,
      },
    );
  }

  @override
  Future<Map<String, dynamic>> getProfile() async {
    final resp = await _api.get('/me/profile');
    return resp.data;
  }

  @override
  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> data) async {
    final resp = await _api.put('/me/profile', body: data);
    return resp.data;
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
    final token = _api.accessToken;
    return token;
  }

  @override
  Future<void> requestRecovery(String email) async {
    await _api.post(
      '/recovery/request',
      body: {'email': email},
      skipAuth: true,
    );
  }

  @override
  Future<bool> verifyRecovery(String token, String code) async {
    final response = await _api.post(
      '/recovery/verify',
      body: {
        'token': token,
        'code': code,
      },
      skipAuth: true,
    );
    return response.data['valid'] as bool? ?? false;
  }

  @override
  Future<void> resetPassword(String token, String newPassword) async {
    await _api.post(
      '/recovery/reset',
      body: {
        'token': token,
        'new_password': newPassword,
      },
      skipAuth: true,
    );
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
    String currentPassword,
    String newPassword,
  ) async {
    await _api.post(
      '/auth/change-password',
      body: {
        'current_password': currentPassword,
        'new_password': newPassword,
      },
    );
  }

  @override
  Future<Map<String, String>> getOAuthUrl(
    String provider,
    String redirectUri,
  ) async {
    final resp = await _api.get(
      '/auth/oauth/$provider/url',
      params: {'redirect_uri': redirectUri},
      skipAuth: true,
    );
    return {
      'auth_url': resp.data['auth_url'] as String,
      'state': resp.data['state'] as String,
    };
  }

  @override
  Future<LoginResult> oauthLogin(
    String provider,
    String code,
    String redirectUri,
    String schoolId,
  ) async {
    final resp = await _api.post(
      '/auth/oauth/login',
      body: {
        'provider': provider,
        'code': code,
        'redirect_uri': redirectUri,
        'school_id': schoolId,
      },
      skipAuth: true,
    );

    final accessToken = resp.data['access_token'] as String;
    _api.setAccessToken(accessToken);

    final refreshToken = resp.data['refresh_token'] as String?;
    if (refreshToken != null) {
      await _tokenStorage.saveRefreshToken(refreshToken);
    }

    return LoginResult(accessToken: accessToken);
  }

  @override
  Future<List<ChildLink>> getChildren() async {
    final resp = await _api.get('/me/children');
    final list =
        resp.data['children'] as List<dynamic>? ?? resp.data as List<dynamic>;
    return list.map((item) {
      final m = item as Map<String, dynamic>;
      return ChildLink(
        userId: m['user_id'] as String,
        fullName: m['full_name'] as String,
        email: m['email'] as String?,
        linkId: m['link_id'] as String,
        linkedAt: m['linked_at'] as String?,
        studentProfile: m['student_profile'] as Map<String, dynamic>?,
      );
    }).toList();
  }
}
