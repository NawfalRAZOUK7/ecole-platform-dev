/// Global Riverpod providers — dependency injection for the app.
///
/// Reference: DEC-E2-002 — Riverpod state management
/// 3-layer dependency chain: Providers → Repositories → API/Cache
/// Phase 5A: Added biometricService, wsClient, local notifications providers.

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/api/ws_client.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/data/local_store/offline_queue.dart';
import 'package:ecole_platform/data/repositories_impl/auth_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/feed_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/notification_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/result_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/invoice_repository_impl.dart';
import 'package:ecole_platform/domain/repositories/auth_repository.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/notification_repository.dart';
import 'package:ecole_platform/domain/repositories/content_repository.dart';
import 'package:ecole_platform/domain/repositories/result_repository.dart';
import 'package:ecole_platform/domain/repositories/invoice_repository.dart';
import 'package:ecole_platform/features/auth/biometric_service.dart';
import 'package:ecole_platform/shared/secure_storage.dart';
import 'package:ecole_platform/shared/push_notifications.dart';

// ── Infrastructure providers ──

final secureStorageProvider = Provider<SecureTokenStorage>((ref) {
  return SecureTokenStorage();
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(secureStorageProvider);
  return ApiClient(
    tokenStorage: storage,
    // In dev, Vite proxy or direct backend.
    // In prod, the actual API URL.
    baseUrl: 'http://localhost:8000',
  );
});

final cacheStoreProvider = Provider<CacheStore>((ref) {
  return CacheStore();
});

final offlineQueueProvider = Provider<OfflineQueue>((ref) {
  return OfflineQueue();
});

/// Shared local notifications plugin — used by push + WS.
final localNotificationsProvider =
    Provider<FlutterLocalNotificationsPlugin>((ref) {
  return FlutterLocalNotificationsPlugin();
});

final pushNotificationProvider = Provider<PushNotificationService>((ref) {
  return PushNotificationService(
    localNotifications: ref.watch(localNotificationsProvider),
  );
});

final biometricServiceProvider = Provider<BiometricService>((ref) {
  return BiometricService();
});

final wsClientProvider = Provider<WsClient>((ref) {
  return WsClient(
    baseUrl: 'http://localhost:8000',
    localNotifications: ref.watch(localNotificationsProvider),
  );
});

// ── Repository providers ──

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepositoryImpl(
    api: ref.watch(apiClientProvider),
    tokenStorage: ref.watch(secureStorageProvider),
  );
});

final feedRepositoryProvider = Provider<FeedRepository>((ref) {
  return FeedRepositoryImpl(
    api: ref.watch(apiClientProvider),
    cache: ref.watch(cacheStoreProvider),
  );
});

final notificationRepositoryProvider = Provider<NotificationRepository>((ref) {
  return NotificationRepositoryImpl(
    api: ref.watch(apiClientProvider),
    cache: ref.watch(cacheStoreProvider),
  );
});

final contentRepositoryProvider = Provider<ContentRepository>((ref) {
  return ContentRepositoryImpl(
    api: ref.watch(apiClientProvider),
    cache: ref.watch(cacheStoreProvider),
  );
});

final resultRepositoryProvider = Provider<ResultRepository>((ref) {
  return ResultRepositoryImpl(
    api: ref.watch(apiClientProvider),
    cache: ref.watch(cacheStoreProvider),
  );
});

final invoiceRepositoryProvider = Provider<InvoiceRepository>((ref) {
  return InvoiceRepositoryImpl(
    api: ref.watch(apiClientProvider),
    cache: ref.watch(cacheStoreProvider),
  );
});
