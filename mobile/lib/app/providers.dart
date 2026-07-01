/// Global Riverpod providers — feature repository layer.
///
/// Core infrastructure providers have moved to `core/di/providers.dart`.
/// This file now only contains feature-specific repository providers
/// and providers that depend on both core + feature layers.
///
/// Reference: DEC-E2-002 — Riverpod state management

import 'package:flutter_riverpod/flutter_riverpod.dart';

// Re-export core providers for backward compatibility during migration.
export 'package:ecole_platform/core/di/providers.dart';

import 'package:ecole_platform/core/di/providers.dart';
import 'package:ecole_platform/data/repositories_impl/auth/auth_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/academic/attendance_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/billing/budget_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/communication/calendar_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content/document_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content/feed_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/communication/notification_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/school/micro_school_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/academic/skills_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/admin/compliance_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/sync/sync_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/reports/financial_health_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content/content_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/academic/result_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/academic/program_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/billing/invoice_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/admin/admin_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/reports/reporting_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/ai/rewards_repository.dart';
import 'package:ecole_platform/data/repositories_impl/lms/teacher_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content/content_library_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/lms/quiz_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/academic/gradebook_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/lms/question_bank_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/lms/rubric_repository_impl.dart';
import 'package:ecole_platform/domain/repositories/auth/auth_repository.dart';
import 'package:ecole_platform/domain/repositories/academic/attendance_repository.dart';
import 'package:ecole_platform/domain/repositories/billing/budget_repository.dart';
import 'package:ecole_platform/domain/repositories/communication/calendar_repository.dart';
import 'package:ecole_platform/domain/repositories/content/document_repository.dart';
import 'package:ecole_platform/domain/repositories/content/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/communication/notification_repository.dart';
import 'package:ecole_platform/domain/repositories/school/micro_school_repository.dart';
import 'package:ecole_platform/domain/repositories/academic/skills_repository.dart';
import 'package:ecole_platform/domain/repositories/admin/compliance_repository.dart';
import 'package:ecole_platform/domain/repositories/sync/sync_repository.dart';
import 'package:ecole_platform/domain/entities/sync/sync.dart';
import 'package:ecole_platform/domain/repositories/reports/financial_health_repository.dart';
import 'package:ecole_platform/domain/repositories/content/content_repository.dart';
import 'package:ecole_platform/domain/repositories/academic/result_repository.dart';
import 'package:ecole_platform/domain/repositories/academic/program_repository.dart';
import 'package:ecole_platform/domain/repositories/billing/invoice_repository.dart';
import 'package:ecole_platform/domain/repositories/admin/admin_repository.dart';
import 'package:ecole_platform/domain/repositories/reports/reporting_repository.dart';
import 'package:ecole_platform/domain/repositories/lms/teacher_repository.dart';
import 'package:ecole_platform/domain/repositories/content/content_library_repository.dart';
import 'package:ecole_platform/domain/repositories/lms/quiz_repository.dart';
import 'package:ecole_platform/domain/repositories/academic/gradebook_repository.dart';
import 'package:ecole_platform/domain/repositories/lms/question_bank_repository.dart';
import 'package:ecole_platform/domain/repositories/lms/rubric_repository.dart';
import 'package:ecole_platform/domain/repositories/ai/rewards_repository.dart';
import 'package:ecole_platform/features/auth/biometric_service.dart';
import 'package:ecole_platform/core/network/connectivity.dart';
import 'package:ecole_platform/shared/services/offline_content_manager.dart';

// ── Cross-cutting providers (depend on core + feature layers) ──

final offlineContentManagerProvider = Provider<OfflineContentManager>((ref) {
  final api = ref.watch(apiClientProvider);
  final cache = ref.watch(cacheStoreProvider);
  final signedUrls = ref.watch(signedUrlCacheProvider);
  final manager =
      OfflineContentManager(api: api, cache: cache, signedUrls: signedUrls);
  ref.onDispose(manager.dispose);
  return manager;
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
    signedUrls: ref.watch(signedUrlCacheProvider),
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

final programRepositoryProvider = Provider<ProgramRepository>((ref) {
  return ProgramRepositoryImpl(
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

final rewardsRepositoryProvider = Provider<RewardsRepository>((ref) {
  return RewardsRepositoryImpl(
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
