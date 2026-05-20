import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/repositories/auth/auth_repository.dart';
import 'package:ecole_platform/features/auth/forgot_password_screen.dart';
import 'package:ecole_platform/features/auth/login_screen.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  testWidgets('LoginScreen renders the login form', (tester) async {
    final authRepository = MockAuthRepository();
    final overrides = _authOverrides(authRepository);

    await pumpApp(tester, const LoginScreen(), overrides: overrides);
    await tester.pumpAndSettle();

    expect(find.text('Connexion'), findsOneWidget);
    expect(find.byType(TextFormField), findsNWidgets(3));
    expect(find.text('Se connecter'), findsOneWidget);
  });

  testWidgets('LoginScreen submits credentials through AuthNotifier',
      (tester) async {
    final authRepository = MockAuthRepository();
    final overrides = _authOverrides(authRepository);

    when(
      () => authRepository.login(
        'parent@ecole.test',
        'secret',
        'school-1',
        deviceName: any(named: 'deviceName'),
        userAgent: any(named: 'userAgent'),
      ),
    ).thenAnswer((_) async => const LoginResult(accessToken: 'access-1'));
    when(() => authRepository.getMe()).thenAnswer((_) async => createUser());

    await pumpApp(tester, const LoginScreen(), overrides: overrides);
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byType(TextFormField).at(0),
      'parent@ecole.test',
    );
    await tester.enterText(find.byType(TextFormField).at(1), 'secret');
    await tester.enterText(find.byType(TextFormField).at(2), 'school-1');
    final loginButton = find.widgetWithText(FilledButton, 'Se connecter');
    await tester.ensureVisible(loginButton);
    await tester.pumpAndSettle();
    await tester.tap(loginButton);
    await tester.pumpAndSettle();

    verify(
      () => authRepository.login(
        'parent@ecole.test',
        'secret',
        'school-1',
        deviceName: any(named: 'deviceName'),
        userAgent: any(named: 'userAgent'),
      ),
    ).called(1);
  });

  testWidgets('ForgotPasswordScreen requests a reset link', (tester) async {
    final authRepository = MockAuthRepository();
    final overrides = _authOverrides(authRepository);

    when(() => authRepository.requestRecovery('parent@ecole.test'))
        .thenAnswer((_) async {});

    await pumpApp(
      tester,
      const ForgotPasswordScreen(),
      overrides: overrides,
    );
    await tester.pumpAndSettle();

    expect(find.text('Send reset link'), findsOneWidget);

    await tester.enterText(find.byType(TextField).first, 'parent@ecole.test');
    await tester.tap(find.text('Send reset link'));
    await tester.pumpAndSettle();

    verify(() => authRepository.requestRecovery('parent@ecole.test')).called(1);
  });
}

List<Override> _authOverrides(MockAuthRepository authRepository) {
  final biometric = MockBiometricService();
  final storage = MockSecureTokenStorage();

  when(() => biometric.isAvailable()).thenAnswer((_) async => false);
  when(() => biometric.isEnabled()).thenAnswer((_) async => false);
  when(() => biometric.resetAttempts()).thenReturn(null);
  when(() => storage.getRefreshToken()).thenAnswer((_) async => null);

  return [
    ...buildMockRepositoryOverrides(authRepository: authRepository),
    biometricServiceProvider.overrideWithValue(biometric),
    secureStorageProvider.overrideWithValue(storage),
  ];
}
