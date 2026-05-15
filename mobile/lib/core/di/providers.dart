/// Core infrastructure providers — cross-cutting dependency injection.
///
/// These providers are framework-agnostic and must not import any feature.
/// Feature-specific providers belong in their respective feature folders.
///
/// Reference: DEC-E2-002 — Riverpod state management

import 'dart:async';

import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/core/network/signed_url_cache.dart';
import 'package:ecole_platform/core/network/ws_client.dart';
import 'package:ecole_platform/core/notifications/push_notifications.dart';
import 'package:ecole_platform/core/storage/cache_store.dart';
import 'package:ecole_platform/core/storage/offline_queue.dart';
import 'package:ecole_platform/core/storage/notifications_store.dart';
import 'package:ecole_platform/core/storage/reports_store.dart';
import 'package:ecole_platform/core/storage/events_store.dart';
import 'package:ecole_platform/core/storage/documents_store.dart';
import 'package:ecole_platform/core/storage/attendance_store.dart';
import 'package:ecole_platform/core/storage/secure_storage.dart';
import 'package:ecole_platform/shared/services/tts_service.dart';

// ── Infrastructure providers ──

final secureStorageProvider = Provider<SecureTokenStorage>((ref) {
  return SecureTokenStorage();
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(secureStorageProvider);
  return ApiClient(
    tokenStorage: storage,
    baseUrl: dotenv.env['API_BASE_URL'] ?? 'http://localhost:8000',
  );
});

final signedUrlCacheProvider = Provider<SignedUrlCache>((ref) {
  final cache = SignedUrlCache(api: ref.watch(apiClientProvider));
  ref.onDispose(cache.clear);
  return cache;
});

final cacheStoreProvider = Provider<CacheStore>((ref) {
  return CacheStore();
});

final offlineQueueProvider = Provider<OfflineQueue>((ref) {
  return OfflineQueue();
});

final notificationsStoreProvider = Provider<NotificationsStore>((ref) {
  return NotificationsStore();
});

final reportsStoreProvider = Provider<ReportsStore>((ref) {
  return ReportsStore();
});

final eventsStoreProvider = Provider<EventsStore>((ref) {
  return EventsStore();
});

final documentsStoreProvider = Provider<DocumentsStore>((ref) {
  return DocumentsStore();
});

final attendanceStoreProvider = Provider<AttendanceStore>((ref) {
  return AttendanceStore(cache: ref.watch(cacheStoreProvider));
});

/// Shared local notifications plugin — used by push + WS.
final localNotificationsProvider =
    Provider<FlutterLocalNotificationsPlugin>((ref) {
  return FlutterLocalNotificationsPlugin();
});

final pushNotificationProvider = Provider<PushNotificationService>((ref) {
  return PushNotificationService(
    apiClient: ref.watch(apiClientProvider),
    localNotifications: ref.watch(localNotificationsProvider),
  );
});

final ttsServiceProvider = Provider<TtsService>((ref) {
  final service = TtsService();
  unawaited(service.init());
  ref.onDispose(() {
    unawaited(service.dispose());
  });
  return service;
});

final wsClientProvider = Provider<WsClient>((ref) {
  return WsClient(
    baseUrl: dotenv.env['API_BASE_URL'] ?? 'http://localhost:8000',
    localNotifications: ref.watch(localNotificationsProvider),
  );
});

class ThemeModeNotifier extends StateNotifier<ThemeMode> {
  final SecureTokenStorage _storage;

  ThemeModeNotifier(this._storage) : super(ThemeMode.system) {
    _restore();
  }

  Future<void> _restore() async {
    final stored = await _storage.getThemeMode();
    state = switch (stored) {
      'light' => ThemeMode.light,
      'dark' => ThemeMode.dark,
      _ => ThemeMode.system,
    };
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    state = mode;
    await _storage.saveThemeMode(mode.name);
  }
}

final themeModeProvider =
    StateNotifierProvider<ThemeModeNotifier, ThemeMode>((ref) {
  return ThemeModeNotifier(ref.watch(secureStorageProvider));
});
