/// Auth state management — Riverpod provider for authentication.
///
/// Reference: S-093 — Auth flow (login/refresh/logout)
/// Phase 5A: 2FA pending state, biometric unlock, device info on login.

import 'dart:io';

import 'package:device_info_plus/device_info_plus.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/user/user.dart';

/// Auth state — immutable value object.
class AuthState {
  final User? user;
  final bool isAuthenticated;
  final bool isLoading;
  final String? error;

  /// 2FA pending state — set when login returns requires_2fa.
  final String? twoFactorTempToken;
  final bool requires2fa;

  /// Biometric state
  final bool biometricAvailable;
  final bool biometricEnabled;

  /// OAuth pending state
  final String? oauthProvider;
  final String? oauthState;
  final String? oauthSchoolId;

  const AuthState({
    this.user,
    this.isAuthenticated = false,
    this.isLoading = false,
    this.error,
    this.twoFactorTempToken,
    this.requires2fa = false,
    this.biometricAvailable = false,
    this.biometricEnabled = false,
    this.oauthProvider,
    this.oauthState,
    this.oauthSchoolId,
  });

  AuthState copyWith({
    User? user,
    bool? isAuthenticated,
    bool? isLoading,
    String? error,
    bool clearError = false,
    bool clearUser = false,
    String? twoFactorTempToken,
    bool? requires2fa,
    bool clear2fa = false,
    bool? biometricAvailable,
    bool? biometricEnabled,
    String? oauthProvider,
    String? oauthState,
    String? oauthSchoolId,
    bool clearOAuth = false,
  }) {
    return AuthState(
      user: clearUser ? null : (user ?? this.user),
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
      twoFactorTempToken:
          clear2fa ? null : (twoFactorTempToken ?? this.twoFactorTempToken),
      requires2fa: clear2fa ? false : (requires2fa ?? this.requires2fa),
      biometricAvailable: biometricAvailable ?? this.biometricAvailable,
      biometricEnabled: biometricEnabled ?? this.biometricEnabled,
      oauthProvider: clearOAuth ? null : (oauthProvider ?? this.oauthProvider),
      oauthState: clearOAuth ? null : (oauthState ?? this.oauthState),
      oauthSchoolId: clearOAuth ? null : (oauthSchoolId ?? this.oauthSchoolId),
    );
  }
}

/// Auth state notifier — manages login/logout/restore/2FA/biometric.
class AuthNotifier extends StateNotifier<AuthState> {
  final Ref _ref;

  AuthNotifier(this._ref) : super(const AuthState(isLoading: true)) {
    _initialize();
  }

  Future<void> _initialize() async {
    // Check biometric availability
    final bio = _ref.read(biometricServiceProvider);
    final bioAvailable = await bio.isAvailable();
    final bioEnabled = bioAvailable ? await bio.isEnabled() : false;

    state = state.copyWith(
      biometricAvailable: bioAvailable,
      biometricEnabled: bioEnabled,
    );

    await _tryRestore();
  }

  /// Try to restore session on app start.
  Future<void> _tryRestore() async {
    try {
      final repo = _ref.read(authRepositoryProvider);
      final token = await _ref.read(secureStorageProvider).getRefreshToken();
      if (token == null) {
        state = state.copyWith(isLoading: false);
        return;
      }

      final api = _ref.read(apiClientProvider);
      api.setAccessToken('pending_refresh');
      final user = await repo.getMe();
      state = state.copyWith(
        user: user,
        isAuthenticated: true,
        isLoading: false,
      );
    } catch (_) {
      state = state.copyWith(isLoading: false);
    }
  }

  /// Get device name and user agent for session tracking (Phase 5A from 2A).
  Future<Map<String, String>> _getDeviceInfo() async {
    final deviceInfo = DeviceInfoPlugin();
    String deviceName = 'Unknown';
    String userAgent = 'EcolePlatform/0.1.0';

    try {
      if (Platform.isAndroid) {
        final android = await deviceInfo.androidInfo;
        deviceName = '${android.brand} ${android.model}';
        userAgent =
            'EcolePlatform/0.1.0 (Android ${android.version.release}; ${android.model})';
      } else if (Platform.isIOS) {
        final ios = await deviceInfo.iosInfo;
        deviceName = ios.name;
        userAgent =
            'EcolePlatform/0.1.0 (iOS ${ios.systemVersion}; ${ios.model})';
      }
    } catch (_) {
      // Fallback to defaults
    }

    return {'device_name': deviceName, 'user_agent': userAgent};
  }

  /// Login with email, password, and school ID.
  Future<void> login(String email, String password, String schoolId) async {
    state = state.copyWith(isLoading: true, clearError: true, clear2fa: true);

    try {
      final repo = _ref.read(authRepositoryProvider);
      final info = await _getDeviceInfo();

      final result = await repo.login(
        email,
        password,
        schoolId,
        deviceName: info['device_name'],
        userAgent: info['user_agent'],
      );

      if (result.requires2fa) {
        state = state.copyWith(
          isLoading: false,
          requires2fa: true,
          twoFactorTempToken: result.tempToken,
        );
        return;
      }

      // Direct login success
      final user = await repo.getMe();
      state = state.copyWith(
        user: user,
        isAuthenticated: true,
        isLoading: false,
        clear2fa: true,
      );

      // Reset biometric failure counter on successful login
      _ref.read(biometricServiceProvider).resetAttempts();
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Verify 2FA code after login.
  Future<void> verify2fa(String code) async {
    if (state.twoFactorTempToken == null) return;
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final repo = _ref.read(authRepositoryProvider);
      await repo.verify2fa(state.twoFactorTempToken!, code);
      final user = await repo.getMe();
      state = AuthState(
        user: user,
        isAuthenticated: true,
        isLoading: false,
        biometricAvailable: state.biometricAvailable,
        biometricEnabled: state.biometricEnabled,
      );

      _ref.read(biometricServiceProvider).resetAttempts();
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Cancel 2FA flow — return to login form.
  void cancel2fa() {
    state = state.copyWith(clear2fa: true, clearError: true);
  }

  /// Attempt biometric unlock (app resume).
  Future<bool> biometricUnlock() async {
    final bio = _ref.read(biometricServiceProvider);
    if (!state.biometricEnabled || bio.shouldFallbackToPassword) return false;

    return await bio.authenticate();
  }

  /// Toggle biometric enabled state.
  Future<void> setBiometricEnabled(bool enabled) async {
    final bio = _ref.read(biometricServiceProvider);
    await bio.setEnabled(enabled);
    state = state.copyWith(biometricEnabled: enabled);
  }

  /// Logout — clear session and tokens.
  Future<void> logout() async {
    try {
      final repo = _ref.read(authRepositoryProvider);
      await repo.logout();
    } catch (_) {
      // Always clear state even if logout API fails
    }
    await _ref.read(cacheStoreProvider).clearAll();
    state = AuthState(
      isLoading: false,
      biometricAvailable: state.biometricAvailable,
      biometricEnabled: state.biometricEnabled,
    );
  }

  /// Start OAuth login — get auth URL and open system browser.
  Future<void> startOAuthLogin(String provider, String schoolId) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final repo = _ref.read(authRepositoryProvider);
      final redirectUri = 'ecoleplatform://auth/callback';
      final result = await repo.getOAuthUrl(provider, redirectUri);

      state = state.copyWith(
        isLoading: false,
        oauthProvider: provider,
        oauthState: result['state'],
        oauthSchoolId: schoolId,
      );

      final url = Uri.parse(result['auth_url']!);
      if (await canLaunchUrl(url)) {
        await launchUrl(url, mode: LaunchMode.externalApplication);
      } else {
        state = state.copyWith(error: 'Cannot open browser for OAuth');
      }
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Complete OAuth login after browser redirect with code.
  Future<void> completeOAuthLogin(
    String provider,
    String code,
    String returnedState,
  ) async {
    if (state.oauthState != returnedState) {
      state = state.copyWith(error: 'Invalid OAuth state', clearOAuth: true);
      return;
    }

    final schoolId = state.oauthSchoolId ?? '';
    state = state.copyWith(isLoading: true, clearError: true, clearOAuth: true);

    try {
      final repo = _ref.read(authRepositoryProvider);
      final redirectUri = 'ecoleplatform://auth/callback';
      await repo.oauthLogin(
        provider,
        code,
        redirectUri,
        schoolId,
      );

      final user = await repo.getMe();
      state = state.copyWith(
        user: user,
        isAuthenticated: true,
        isLoading: false,
      );

      _ref.read(biometricServiceProvider).resetAttempts();
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  /// Clear the error message.
  void clearError() {
    state = state.copyWith(clearError: true);
  }
}

/// Auth state provider.
final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref);
});
