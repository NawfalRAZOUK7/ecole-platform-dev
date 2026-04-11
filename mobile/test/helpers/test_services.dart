import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:local_auth/local_auth.dart';

import 'package:ecole_platform/data/api/ws_client.dart';
import 'package:ecole_platform/domain/entities/sync.dart';
import 'package:ecole_platform/features/auth/biometric_service.dart';
import 'package:ecole_platform/shared/connectivity_service.dart';
import 'package:ecole_platform/shared/push_notifications.dart';
import 'package:ecole_platform/shared/secure_storage.dart';

class TestPushNotificationService implements PushNotificationService {
  @override
  int badgeCount = 0;

  @override
  void Function(RemoteMessage message)? onForegroundMessage;

  @override
  PushDeepLink? pendingDeepLink;

  @override
  void clearDeepLink() {
    pendingDeepLink = null;
  }

  @override
  Future<void> initialize() async {}

  @override
  void resetBadge() {
    badgeCount = 0;
  }

  @override
  Future<void> syncTokenRegistration() async {}
}

class TestWsClient implements WsClient {
  final Set<WsListener> _listeners = {};

  @override
  int badgeCount = 0;

  @override
  void Function(WsEvent event)? onEvent;

  @override
  void connect(String accessToken) {}

  @override
  void disconnect() {}

  @override
  void resetBadge() {
    badgeCount = 0;
  }

  @override
  VoidCallback subscribe(WsListener listener) {
    _listeners.add(listener);
    return () => _listeners.remove(listener);
  }
}

class TestConnectivityService implements ConnectivityService {
  @override
  String get deviceId => 'test-device';

  @override
  SyncIndicatorState get indicator => const SyncIndicatorState(
        online: true,
        syncing: false,
        pendingCount: 0,
        failedCount: 0,
      );

  @override
  Stream<SyncIndicatorState> get indicatorStream =>
      Stream<SyncIndicatorState>.empty();

  @override
  bool get isOnline => true;

  @override
  void dispose() {}

  @override
  Future<void> initialize() async {}
}

class TestSecureTokenStorage implements SecureTokenStorage {
  String? _refreshToken;
  String? _csrfToken;
  String? _themeMode;
  String? _localeCode;

  @override
  Future<void> clearAll() async {
    _refreshToken = null;
    _csrfToken = null;
  }

  @override
  Future<String?> getCsrfToken() async {
    return _csrfToken;
  }

  @override
  Future<String?> getRefreshToken() async {
    return _refreshToken;
  }

  @override
  Future<String?> getThemeMode() async {
    return _themeMode;
  }

  @override
  Future<String?> getLocaleCode() async {
    return _localeCode;
  }

  @override
  Future<void> saveCsrfToken(String token) async {
    _csrfToken = token;
  }

  @override
  Future<void> saveRefreshToken(String token) async {
    _refreshToken = token;
  }

  @override
  Future<void> saveThemeMode(String mode) async {
    _themeMode = mode;
  }

  @override
  Future<void> saveLocaleCode(String localeCode) async {
    _localeCode = localeCode;
  }
}

class TestBiometricService implements BiometricService {
  bool _enabled = false;

  @override
  Future<bool> authenticate(
      {String reason = 'Veuillez vous authentifier'}) async {
    return false;
  }

  @override
  Future<void> clear() async {
    _enabled = false;
  }

  @override
  Future<List<BiometricType>> getAvailableTypes() async {
    return const [];
  }

  @override
  Future<bool> isAvailable() async {
    return false;
  }

  @override
  Future<bool> isEnabled() async {
    return _enabled;
  }

  @override
  void resetAttempts() {}

  @override
  Future<void> setEnabled(bool enabled) async {
    _enabled = enabled;
  }

  @override
  bool get shouldFallbackToPassword => false;
}
