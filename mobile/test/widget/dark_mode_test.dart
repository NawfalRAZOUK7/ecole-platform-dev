import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/admin/compliance.dart';
import 'package:ecole_platform/domain/entities/lms/question_bank.dart';
import 'package:ecole_platform/domain/common/pagination.dart';
import 'package:ecole_platform/features/auth/forgot_password_screen.dart';
import 'package:ecole_platform/features/auth/login_screen.dart';
import 'package:ecole_platform/features/admin/compliance/compliance_dashboard_screen.dart';
import 'package:ecole_platform/features/billing/invoices/invoices_screen.dart';
import 'package:ecole_platform/features/lms/question_bank/question_bank_screen.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  testWidgets('LoginScreen renders correctly in dark mode', (tester) async {
    final authRepository = MockAuthRepository();

    await pumpApp(
      tester,
      const LoginScreen(),
      themeMode: ThemeMode.dark,
      overrides: _authDarkOverrides(authRepository),
    );
    await tester.pumpAndSettle();

    _expectDarkMaterialApp(tester);
    _expectReadableText(tester, find.text('Connexion'));
  });

  testWidgets('InvoicesScreen renders correctly in dark mode', (tester) async {
    final repository = MockInvoiceRepository();
    when(() => repository.getInvoices()).thenAnswer(
      (_) async => PaginatedList(items: [createInvoice()], hasMore: false),
    );

    await pumpApp(
      tester,
      const InvoicesScreen(),
      themeMode: ThemeMode.dark,
      overrides: buildMockRepositoryOverrides(invoiceRepository: repository),
    );
    await tester.pumpAndSettle();

    _expectDarkMaterialApp(tester);
    _expectReadableText(tester, find.text('Monthly tuition'));
  });

  testWidgets('ForgotPasswordScreen renders correctly in dark mode',
      (tester) async {
    final authRepository = MockAuthRepository();

    await pumpApp(
      tester,
      const ForgotPasswordScreen(),
      themeMode: ThemeMode.dark,
      overrides: _authDarkOverrides(authRepository),
    );
    await tester.pumpAndSettle();

    _expectDarkMaterialApp(tester);
    _expectReadableText(tester, find.text('Send reset link'));
  });

  testWidgets('ComplianceDashboardScreen renders correctly in dark mode',
      (tester) async {
    final repository = MockComplianceRepository();
    when(
      () => repository.getDashboard(
        academicYearId: any(named: 'academicYearId'),
      ),
    ).thenAnswer(
      (_) async => const ComplianceDashboardData(
        coverageRate: 70,
        objectivesCoveredRate: 75,
        missingCoverageRate: 30,
        metrics: [ComplianceMetric(label: 'Coverage gap', value: 70)],
      ),
    );

    await pumpApp(
      tester,
      const ComplianceDashboardScreen(),
      themeMode: ThemeMode.dark,
      overrides: buildMockRepositoryOverrides(complianceRepository: repository),
    );
    await tester.pumpAndSettle();

    _expectDarkMaterialApp(tester);
    _expectReadableText(tester, find.text('Coverage gap'));
  });

  testWidgets('QuestionBankScreen renders correctly in dark mode',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(1200, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final repository = MockQuestionBankRepository();
    when(
      () =>
          repository.listQuestions(subject: null, type: null, difficulty: null),
    ).thenAnswer((_) async => const [_question]);
    when(() => repository.getStats()).thenAnswer(
      (_) async => const QuestionBankStats(
        total: 1,
        bySubject: {'Mathematics': 1},
        byType: {'mcq': 1},
        byDifficulty: {'medium': 1},
      ),
    );

    await pumpApp(
      tester,
      const QuestionBankScreen(),
      themeMode: ThemeMode.dark,
      overrides: buildMockRepositoryOverrides(
        questionBankRepository: repository,
      ),
    );
    await tester.pumpAndSettle();

    _expectDarkMaterialApp(tester);
    _expectReadableText(tester, find.text('What is 2 + 2?'));
  });
}

List<Override> _authDarkOverrides(MockAuthRepository authRepository) {
  final biometric = MockBiometricService();
  final storage = MockSecureTokenStorage();

  when(() => storage.getRefreshToken()).thenAnswer((_) async => null);
  when(() => biometric.isAvailable()).thenAnswer((_) async => false);
  when(() => biometric.isEnabled()).thenAnswer((_) async => false);

  return [
    ...buildMockRepositoryOverrides(authRepository: authRepository),
    biometricServiceProvider.overrideWithValue(biometric),
    secureStorageProvider.overrideWithValue(storage),
  ];
}

void _expectDarkMaterialApp(WidgetTester tester) {
  final app = tester.widget<MaterialApp>(find.byType(MaterialApp));
  expect(app.themeMode, ThemeMode.dark);
}

void _expectReadableText(WidgetTester tester, Finder finder) {
  final element = tester.element(finder);
  final theme = Theme.of(element);
  final text = tester.widget<Text>(finder);
  final effectiveColor = text.style?.color ??
      DefaultTextStyle.of(element).style.color ??
      theme.colorScheme.onSurface;
  expect(effectiveColor, isNot(theme.colorScheme.surface));
}

const _question = QuestionBankQuestion(
  id: 'question-1',
  subject: 'Mathematics',
  type: 'mcq',
  difficulty: 'medium',
  text: 'What is 2 + 2?',
  choices: [
    QuestionBankChoice(id: 'choice-1', text: '4', isCorrect: true),
  ],
  correctAnswer: '4',
  tags: ['math'],
  createdBy: 'teacher-1',
  createdAt: '2026-04-12T08:00:00Z',
);
