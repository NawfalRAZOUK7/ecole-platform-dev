/// Global Riverpod providers — dependency injection for the app.
///
/// Reference: DEC-E2-002 — Riverpod state management
/// 3-layer dependency chain: Providers → Repositories → API/Cache
/// Phase 5A: Added biometricService, wsClient, local notifications providers.
/// Phase 5B: Added admin + teacher repository providers.
/// Phase 10C: Added content library + quiz repository providers.

import 'dart:async';

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/api/ws_client.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/data/local_store/notifications_store.dart';
import 'package:ecole_platform/data/local_store/offline_queue.dart';
import 'package:ecole_platform/data/local_store/reports_store.dart';
import 'package:ecole_platform/data/local_store/events_store.dart';
import 'package:ecole_platform/data/local_store/documents_store.dart';
import 'package:ecole_platform/data/local_store/attendance_store.dart';
import 'package:ecole_platform/data/repositories_impl/auth_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/attendance_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/budget_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/calendar_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/document_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/feed_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/notification_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/micro_school_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/skills_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/compliance_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/sync_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/financial_health_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/result_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/invoice_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/admin_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/reporting_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/teacher_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content_library_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/quiz_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/gradebook_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/question_bank_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/rubric_repository_impl.dart';
import 'package:ecole_platform/domain/repositories/auth_repository.dart';
import 'package:ecole_platform/domain/repositories/attendance_repository.dart';
import 'package:ecole_platform/domain/repositories/budget_repository.dart';
import 'package:ecole_platform/domain/repositories/calendar_repository.dart';
import 'package:ecole_platform/domain/repositories/document_repository.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/notification_repository.dart';
import 'package:ecole_platform/domain/repositories/micro_school_repository.dart';
import 'package:ecole_platform/domain/repositories/skills_repository.dart';
import 'package:ecole_platform/domain/repositories/compliance_repository.dart';
import 'package:ecole_platform/domain/repositories/sync_repository.dart';
import 'package:ecole_platform/domain/entities/sync.dart';
import 'package:ecole_platform/domain/repositories/financial_health_repository.dart';
import 'package:ecole_platform/domain/repositories/content_repository.dart';
import 'package:ecole_platform/domain/repositories/result_repository.dart';
import 'package:ecole_platform/domain/repositories/invoice_repository.dart';
import 'package:ecole_platform/domain/repositories/admin_repository.dart';
import 'package:ecole_platform/domain/repositories/reporting_repository.dart';
import 'package:ecole_platform/domain/repositories/teacher_repository.dart';
import 'package:ecole_platform/domain/repositories/content_library_repository.dart';
import 'package:ecole_platform/domain/repositories/quiz_repository.dart';
import 'package:ecole_platform/domain/repositories/gradebook_repository.dart';
import 'package:ecole_platform/domain/repositories/question_bank_repository.dart';
import 'package:ecole_platform/domain/repositories/rubric_repository.dart';
import 'package:ecole_platform/features/auth/biometric_service.dart';
import 'package:ecole_platform/shared/secure_storage.dart';
import 'package:ecole_platform/shared/connectivity_service.dart';
import 'package:ecole_platform/shared/push_notifications.dart';
import 'package:ecole_platform/shared/services/tts_service.dart';

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

final connectivityServiceProvider = Provider<ConnectivityService>((ref) {
  return ConnectivityService(
    api: ref.watch(apiClientProvider),
    queue: ref.watch(offlineQueueProvider),
    cache: ref.watch(cacheStoreProvider),
    syncRepository: ref.watch(syncRepositoryProvider),
  );
});

final biometricServiceProvider = Provider<BiometricService>((ref) {
  return BiometricService();
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
    baseUrl: 'http://localhost:8000',
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

final calendarRepositoryProvider = Provider<CalendarRepository>((ref) {
  return CalendarRepositoryImpl(
    api: ref.watch(apiClientProvider),
    eventsStore: ref.watch(eventsStoreProvider),
  );
});

final documentRepositoryProvider = Provider<DocumentRepository>((ref) {
  return DocumentRepositoryImpl(
    api: ref.watch(apiClientProvider),
    documentsStore: ref.watch(documentsStoreProvider),
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

final gradebookRepositoryProvider = Provider<GradebookRepository>((ref) {
  return GradebookRepositoryImpl(
    api: ref.watch(apiClientProvider),
    cache: ref.watch(cacheStoreProvider),
  );
});

final questionBankRepositoryProvider = Provider<QuestionBankRepository>((ref) {
  return QuestionBankRepositoryImpl(
    api: ref.watch(apiClientProvider),
  );
});

final rubricRepositoryProvider = Provider<RubricRepository>((ref) {
  return RubricRepositoryImpl(
    api: ref.watch(apiClientProvider),
  );
});

final attendanceRepositoryProvider = Provider<AttendanceRepository>((ref) {
  return AttendanceRepositoryImpl(
    api: ref.watch(apiClientProvider),
    store: ref.watch(attendanceStoreProvider),
  );
});

final budgetRepositoryProvider = Provider<BudgetRepository>((ref) {
  return BudgetRepositoryImpl(api: ref.watch(apiClientProvider));
});

final microSchoolRepositoryProvider = Provider<MicroSchoolRepository>((ref) {
  return MicroSchoolRepositoryImpl(api: ref.watch(apiClientProvider));
});

final skillsRepositoryProvider = Provider<SkillsRepository>((ref) {
  return SkillsRepositoryImpl(api: ref.watch(apiClientProvider));
});

final complianceRepositoryProvider = Provider<ComplianceRepository>((ref) {
  return ComplianceRepositoryImpl(api: ref.watch(apiClientProvider));
});

final syncRepositoryProvider = Provider<SyncRepository>((ref) {
  return SyncRepositoryImpl(api: ref.watch(apiClientProvider));
});

final financialHealthRepositoryProvider =
    Provider<FinancialHealthRepository>((ref) {
  return FinancialHealthRepositoryImpl(api: ref.watch(apiClientProvider));
});

final syncIndicatorProvider = StreamProvider<SyncIndicatorState>((ref) async* {
  final service = ref.watch(connectivityServiceProvider);
  yield service.indicator;
  yield* service.indicatorStream;
});
