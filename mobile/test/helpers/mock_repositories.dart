import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/repositories/admin/admin_repository.dart';
import 'package:ecole_platform/domain/repositories/academic/attendance_repository.dart';
import 'package:ecole_platform/domain/repositories/auth/auth_repository.dart';
import 'package:ecole_platform/domain/repositories/billing/budget_repository.dart';
import 'package:ecole_platform/domain/repositories/communication/calendar_repository.dart';
import 'package:ecole_platform/domain/repositories/content/content_library_repository.dart';
import 'package:ecole_platform/domain/repositories/content/content_repository.dart';
import 'package:ecole_platform/domain/repositories/content/document_repository.dart';
import 'package:ecole_platform/domain/repositories/content/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/academic/gradebook_repository.dart';
import 'package:ecole_platform/domain/repositories/billing/invoice_repository.dart';
import 'package:ecole_platform/domain/repositories/school/micro_school_repository.dart';
import 'package:ecole_platform/domain/repositories/communication/notification_repository.dart';
import 'package:ecole_platform/domain/repositories/lms/quiz_repository.dart';
import 'package:ecole_platform/domain/repositories/reports/reporting_repository.dart';
import 'package:ecole_platform/domain/repositories/academic/result_repository.dart';
import 'package:ecole_platform/domain/repositories/academic/skills_repository.dart';
import 'package:ecole_platform/domain/repositories/lms/teacher_repository.dart';
import 'package:ecole_platform/domain/repositories/admin/compliance_repository.dart';
import 'package:ecole_platform/domain/repositories/reports/financial_health_repository.dart';
import 'package:ecole_platform/domain/repositories/lms/question_bank_repository.dart';
import 'package:ecole_platform/domain/repositories/academic/program_repository.dart';

class MockAdminRepository extends Mock implements AdminRepository {}

class MockAttendanceRepository extends Mock implements AttendanceRepository {}

class MockAuthRepository extends Mock implements AuthRepository {}

class MockBudgetRepository extends Mock implements BudgetRepository {}

class MockCalendarRepository extends Mock implements CalendarRepository {}

class MockContentLibraryRepository extends Mock
    implements ContentLibraryRepository {}

class MockContentRepository extends Mock implements ContentRepository {}

class MockDocumentRepository extends Mock implements DocumentRepository {}

class MockFeedRepository extends Mock implements FeedRepository {}

class MockGradebookRepository extends Mock implements GradebookRepository {}

class MockInvoiceRepository extends Mock implements InvoiceRepository {}

class MockMicroSchoolRepository extends Mock implements MicroSchoolRepository {}

class MockNotificationRepository extends Mock
    implements NotificationRepository {}

class MockQuizRepository extends Mock implements QuizRepository {}

class MockReportingRepository extends Mock implements ReportingRepository {}

class MockResultRepository extends Mock implements ResultRepository {}

class MockSkillsRepository extends Mock implements SkillsRepository {}

class MockTeacherRepository extends Mock implements TeacherRepository {}

class MockComplianceRepository extends Mock implements ComplianceRepository {}

class MockFinancialHealthRepository extends Mock
    implements FinancialHealthRepository {}

class MockQuestionBankRepository extends Mock
    implements QuestionBankRepository {}

class MockProgramRepository extends Mock implements ProgramRepository {}

List<Override> buildMockRepositoryOverrides({
  AdminRepository? adminRepository,
  AttendanceRepository? attendanceRepository,
  AuthRepository? authRepository,
  BudgetRepository? budgetRepository,
  CalendarRepository? calendarRepository,
  ContentLibraryRepository? contentLibraryRepository,
  ContentRepository? contentRepository,
  DocumentRepository? documentRepository,
  FeedRepository? feedRepository,
  GradebookRepository? gradebookRepository,
  InvoiceRepository? invoiceRepository,
  MicroSchoolRepository? microSchoolRepository,
  NotificationRepository? notificationRepository,
  QuizRepository? quizRepository,
  ReportingRepository? reportingRepository,
  ResultRepository? resultRepository,
  SkillsRepository? skillsRepository,
  TeacherRepository? teacherRepository,
  ComplianceRepository? complianceRepository,
  FinancialHealthRepository? financialHealthRepository,
  QuestionBankRepository? questionBankRepository,
  ProgramRepository? programRepository,
}) {
  final overrides = <Override>[];

  if (adminRepository != null) {
    overrides.add(adminRepositoryProvider.overrideWithValue(adminRepository));
  }
  if (attendanceRepository != null) {
    overrides.add(
      attendanceRepositoryProvider.overrideWithValue(attendanceRepository),
    );
  }
  if (authRepository != null) {
    overrides.add(authRepositoryProvider.overrideWithValue(authRepository));
  }
  if (budgetRepository != null) {
    overrides.add(budgetRepositoryProvider.overrideWithValue(budgetRepository));
  }
  if (calendarRepository != null) {
    overrides.add(
      calendarRepositoryProvider.overrideWithValue(calendarRepository),
    );
  }
  if (contentLibraryRepository != null) {
    overrides.add(
      contentLibraryRepositoryProvider
          .overrideWithValue(contentLibraryRepository),
    );
  }
  if (contentRepository != null) {
    overrides
        .add(contentRepositoryProvider.overrideWithValue(contentRepository));
  }
  if (documentRepository != null) {
    overrides.add(
      documentRepositoryProvider.overrideWithValue(documentRepository),
    );
  }
  if (feedRepository != null) {
    overrides.add(feedRepositoryProvider.overrideWithValue(feedRepository));
  }
  if (gradebookRepository != null) {
    overrides.add(
      gradebookRepositoryProvider.overrideWithValue(gradebookRepository),
    );
  }
  if (invoiceRepository != null) {
    overrides
        .add(invoiceRepositoryProvider.overrideWithValue(invoiceRepository));
  }
  if (microSchoolRepository != null) {
    overrides.add(
      microSchoolRepositoryProvider.overrideWithValue(microSchoolRepository),
    );
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
  if (skillsRepository != null) {
    overrides.add(skillsRepositoryProvider.overrideWithValue(skillsRepository));
  }
  if (teacherRepository != null) {
    overrides
        .add(teacherRepositoryProvider.overrideWithValue(teacherRepository));
  }
  if (complianceRepository != null) {
    overrides.add(
      complianceRepositoryProvider.overrideWithValue(complianceRepository),
    );
  }
  if (financialHealthRepository != null) {
    overrides.add(
      financialHealthRepositoryProvider
          .overrideWithValue(financialHealthRepository),
    );
  }
  if (questionBankRepository != null) {
    overrides.add(
      questionBankRepositoryProvider.overrideWithValue(questionBankRepository),
    );
  }
  if (programRepository != null) {
    overrides
        .add(programRepositoryProvider.overrideWithValue(programRepository));
  }

  return overrides;
}
