import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/repositories/admin_repository.dart';
import 'package:ecole_platform/domain/repositories/auth_repository.dart';
import 'package:ecole_platform/domain/repositories/calendar_repository.dart';
import 'package:ecole_platform/domain/repositories/content_library_repository.dart';
import 'package:ecole_platform/domain/repositories/content_repository.dart';
import 'package:ecole_platform/domain/repositories/document_repository.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/invoice_repository.dart';
import 'package:ecole_platform/domain/repositories/notification_repository.dart';
import 'package:ecole_platform/domain/repositories/quiz_repository.dart';
import 'package:ecole_platform/domain/repositories/reporting_repository.dart';
import 'package:ecole_platform/domain/repositories/result_repository.dart';
import 'package:ecole_platform/domain/repositories/teacher_repository.dart';

class MockAdminRepository extends Mock implements AdminRepository {}

class MockAuthRepository extends Mock implements AuthRepository {}

class MockCalendarRepository extends Mock implements CalendarRepository {}

class MockContentLibraryRepository extends Mock
    implements ContentLibraryRepository {}

class MockContentRepository extends Mock implements ContentRepository {}

class MockDocumentRepository extends Mock implements DocumentRepository {}

class MockFeedRepository extends Mock implements FeedRepository {}

class MockInvoiceRepository extends Mock implements InvoiceRepository {}

class MockNotificationRepository extends Mock
    implements NotificationRepository {}

class MockQuizRepository extends Mock implements QuizRepository {}

class MockReportingRepository extends Mock implements ReportingRepository {}

class MockResultRepository extends Mock implements ResultRepository {}

class MockTeacherRepository extends Mock implements TeacherRepository {}

List<Override> buildMockRepositoryOverrides({
  AdminRepository? adminRepository,
  AuthRepository? authRepository,
  CalendarRepository? calendarRepository,
  ContentLibraryRepository? contentLibraryRepository,
  ContentRepository? contentRepository,
  DocumentRepository? documentRepository,
  FeedRepository? feedRepository,
  InvoiceRepository? invoiceRepository,
  NotificationRepository? notificationRepository,
  QuizRepository? quizRepository,
  ReportingRepository? reportingRepository,
  ResultRepository? resultRepository,
  TeacherRepository? teacherRepository,
}) {
  final overrides = <Override>[];

  if (adminRepository != null) {
    overrides.add(adminRepositoryProvider.overrideWithValue(adminRepository));
  }
  if (authRepository != null) {
    overrides.add(authRepositoryProvider.overrideWithValue(authRepository));
  }
  if (calendarRepository != null) {
    overrides.add(
      calendarRepositoryProvider.overrideWithValue(calendarRepository),
    );
  }
  if (contentLibraryRepository != null) {
    overrides.add(
      contentLibraryRepositoryProvider.overrideWithValue(contentLibraryRepository),
    );
  }
  if (contentRepository != null) {
    overrides.add(contentRepositoryProvider.overrideWithValue(contentRepository));
  }
  if (documentRepository != null) {
    overrides.add(
      documentRepositoryProvider.overrideWithValue(documentRepository),
    );
  }
  if (feedRepository != null) {
    overrides.add(feedRepositoryProvider.overrideWithValue(feedRepository));
  }
  if (invoiceRepository != null) {
    overrides.add(invoiceRepositoryProvider.overrideWithValue(invoiceRepository));
  }
  if (notificationRepository != null) {
    overrides.add(
      notificationRepositoryProvider.overrideWithValue(notificationRepository),
    );
  }
  if (quizRepository != null) {
    overrides.add(quizRepositoryProvider.overrideWithValue(quizRepository));
  }
  if (reportingRepository != null) {
    overrides.add(
      reportingRepositoryProvider.overrideWithValue(reportingRepository),
    );
  }
  if (resultRepository != null) {
    overrides.add(resultRepositoryProvider.overrideWithValue(resultRepository));
  }
  if (teacherRepository != null) {
    overrides.add(teacherRepositoryProvider.overrideWithValue(teacherRepository));
  }

  return overrides;
}
