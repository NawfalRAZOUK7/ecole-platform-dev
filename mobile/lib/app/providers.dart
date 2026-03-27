/// Global Riverpod providers — dependency injection for the app.
///
/// Reference: DEC-E2-002 — Riverpod state management
/// 3-layer dependency chain: Providers → Repositories → API/Cache
/// Phase 5A: Added biometricService, wsClient, local notifications providers.
/// Phase 5B: Added admin + teacher repository providers.
/// Phase 10C: Added content library + quiz repository providers.

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/api/ws_client.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/data/local_store/notifications_store.dart';
import 'package:ecole_platform/data/local_store/offline_queue.dart';
import 'package:ecole_platform/data/local_store/reports_store.dart';
import 'package:ecole_platform/data/repositories_impl/auth_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/feed_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/notification_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/result_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/invoice_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/admin_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/reporting_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/teacher_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content_library_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/quiz_repository_impl.dart';
import 'package:ecole_platform/domain/repositories/auth_repository.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/notification_repository.dart';
import 'package:ecole_platform/domain/repositories/content_repository.dart';
import 'package:ecole_platform/domain/repositories/result_repository.dart';
import 'package:ecole_platform/domain/repositories/invoice_repository.dart';
import 'package:ecole_platform/domain/repositories/admin_repository.dart';
import 'package:ecole_platform/domain/repositories/reporting_repository.dart';
import 'package:ecole_platform/domain/repositories/teacher_repository.dart';
import 'package:ecole_platform/domain/repositories/content_library_repository.dart';
import 'package:ecole_platform/domain/repositories/quiz_repository.dart';
import 'package:ecole_platform/features/auth/biometric_service.dart';
import 'package:ecole_platform/shared/secure_storage.dart';
import 'package:ecole_platform/shared/connectivity_service.dart';
import 'package:ecole_platform/shared/push_notifications.dart';

// ── Infrastructure providers ──

final secureStorageProvider = Provider<SecureTokenStorage>((ref) {
  return SecureTokenStorage();
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final storage = ref.watch(secureStorageProvider);
  return ApiClient(
    tokenStorage: storage,
    baseUrl: 'http://localhost:8000',
  );
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

final connectivityServiceProvider = Provider<ConnectivityService>((ref) {
  return ConnectivityService(
    api: ref.watch(apiClientProvider),
    queue: ref.watch(offlineQueueProvider),
    cache: ref.watch(cacheStoreProvider),
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
    notificationsStore: ref.watch(notificationsStoreProvider),
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

final adminRepositoryProvider = Provider<AdminRepository>((ref) {
  return AdminRepositoryImpl(
    api: ref.watch(apiClientProvider),
  );
});

final reportingRepositoryProvider = Provider<ReportingRepository>((ref) {
  return ReportingRepositoryImpl(
    api: ref.watch(apiClientProvider),
    reportsStore: ref.watch(reportsStoreProvider),
  );
});

final teacherRepositoryProvider = Provider<TeacherRepository>((ref) {
  return TeacherRepositoryImpl(
    api: ref.watch(apiClientProvider),
  );
});

// Phase 10C: Content library + quiz repositories

final contentLibraryRepositoryProvider =
    Provider<ContentLibraryRepository>((ref) {
  return ContentLibraryRepositoryImpl(
    api: ref.watch(apiClientProvider),
    cache: ref.watch(cacheStoreProvider),
  );
});

final quizRepositoryProvider = Provider<QuizRepository>((ref) {
  return QuizRepositoryImpl(
    api: ref.watch(apiClientProvider),
    cache: ref.watch(cacheStoreProvider),
  );
});
