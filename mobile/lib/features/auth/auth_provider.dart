/// Auth state management — Riverpod provider for authentication.
///
/// Reference: S-093 — Auth flow (login/refresh/logout)
/// Manages auth state, user profile, and session lifecycle.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/user.dart';

/// Auth state — immutable value object.
class AuthState {
  final User? user;
  final bool isAuthenticated;
  final bool isLoading;
  final String? error;

  const AuthState({
    this.user,
    this.isAuthenticated = false,
    this.isLoading = false,
    this.error,
  });

  AuthState copyWith({
    User? user,
    bool? isAuthenticated,
    bool? isLoading,
    String? error,
    bool clearError = false,
    bool clearUser = false,
  }) {
    return AuthState(
      user: clearUser ? null : (user ?? this.user),
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

/// Auth state notifier — manages login/logout/restore.
class AuthNotifier extends StateNotifier<AuthState> {
  final Ref _ref;

  AuthNotifier(this._ref) : super(const AuthState(isLoading: true)) {
    _tryRestore();
  }

  /// Try to restore session on app start.
  Future<void> _tryRestore() async {
    try {
      final repo = _ref.read(authRepositoryProvider);
      final token = await _ref.read(secureStorageProvider).getRefreshToken();
      if (token == null) {
        state = const AuthState(isLoading: false);
        return;
      }

      // Try refresh
      final api = _ref.read(apiClientProvider);
      // The refresh will happen through the API client
      // For now, try to get /me directly — the API client will auto-refresh
      api.setAccessToken('pending_refresh');
      final user = await repo.getMe();
      state = AuthState(
        user: user,
        isAuthenticated: true,
        isLoading: false,
      );
    } catch (_) {
      state = const AuthState(isLoading: false);
    }
  }

  /// Login with email, password, and school ID.
  Future<void> login(String email, String password, String schoolId) async {
    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final repo = _ref.read(authRepositoryProvider);
      await repo.login(email, password, schoolId);
      final user = await repo.getMe();
      state = AuthState(
        user: user,
        isAuthenticated: true,
        isLoading: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  /// Logout — clear session and tokens.
  Future<void> logout() async {
    try {
      final repo = _ref.read(authRepositoryProvider);
      await repo.logout();
    } catch (_) {
      // Always clear state even if logout API fails
    }
    // Clear offline cache on logout
    await _ref.read(cacheStoreProvider).clearAll();
    state = const AuthState(isLoading: false);
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
