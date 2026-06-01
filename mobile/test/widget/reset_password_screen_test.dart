import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/auth/reset_password_screen.dart';
import 'package:ecole_platform/domain/repositories/auth/auth_repository.dart';

import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

class _MockAuthRepository extends Mock implements AuthRepository {}

List<Override> _overrides(_MockAuthRepository auth) {
  final biometric = MockBiometricService();
  final storage = MockSecureTokenStorage();
  when(() => biometric.isAvailable()).thenAnswer((_) async => false);
  when(() => biometric.isEnabled()).thenAnswer((_) async => false);
  when(() => biometric.resetAttempts()).thenReturn(null);
  when(() => storage.getRefreshToken()).thenAnswer((_) async => null);
  return [
    ...buildMockRepositoryOverrides(authRepository: auth),
    biometricServiceProvider.overrideWithValue(biometric),
    secureStorageProvider.overrideWithValue(storage),
  ];
}

void main() {
  late _MockAuthRepository mockAuth;

  setUpAll(registerTestFallbacks);

  setUp(() {
    mockAuth = _MockAuthRepository();
    when(() => mockAuth.verifyRecovery(any(), any()))
        .thenAnswer((_) async => true);
    when(() => mockAuth.resetPassword(any(), any()))
        .thenAnswer((_) async {});
  });

  group('ResetPasswordScreen', () {
    testWidgets('renders at least two input fields', (tester) async {
      await pumpApp(
        tester,
        const ResetPasswordScreen(),
        overrides: _overrides(mockAuth),
      );
      await tester.pumpAndSettle();

      expect(find.byType(TextField), findsAtLeastNWidgets(2));
    });

    testWidgets('pre-fills token from widget param', (tester) async {
      await pumpApp(
        tester,
        const ResetPasswordScreen(token: 'abc-xyz'),
        overrides: _overrides(mockAuth),
      );
      await tester.pumpAndSettle();

      final fields = tester.widgetList<TextField>(find.byType(TextField)).toList();
      expect(fields.first.controller?.text, 'abc-xyz');
    });

    testWidgets('renders the lock_reset icon in the submit button', (tester) async {
      await pumpApp(
        tester,
        const ResetPasswordScreen(),
        overrides: _overrides(mockAuth),
      );
      await tester.pumpAndSettle();

      // Scroll to the bottom so the button is visible
      await tester.drag(find.byType(ListView), const Offset(0, -500));
      await tester.pump();

      expect(find.byIcon(Icons.lock_reset_outlined), findsOneWidget);
    });

    testWidgets('submit without code calls resetPassword', (tester) async {
      await pumpApp(
        tester,
        const ResetPasswordScreen(token: 'tok-1'),
        overrides: _overrides(mockAuth),
      );
      await tester.pumpAndSettle();

      // Enter password in the third TextField (index 2)
      await tester.enterText(find.byType(TextField).at(2), 'NewPass123!');
      await tester.pump();

      // Scroll down and tap the submit button (identified by icon)
      await tester.drag(find.byType(ListView), const Offset(0, -500));
      await tester.pump();

      await tester.tap(find.byIcon(Icons.lock_reset_outlined));
      await tester.pumpAndSettle();

      verify(() => mockAuth.resetPassword('tok-1', 'NewPass123!')).called(1);
    });

    testWidgets('with verification code calls verifyRecovery then resetPassword', (tester) async {
      await pumpApp(
        tester,
        const ResetPasswordScreen(token: 'tok-1'),
        overrides: _overrides(mockAuth),
      );
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField).at(1), 'CODE123');
      await tester.enterText(find.byType(TextField).at(2), 'Pass!');
      await tester.pump();

      await tester.drag(find.byType(ListView), const Offset(0, -500));
      await tester.pump();

      await tester.tap(find.byIcon(Icons.lock_reset_outlined));
      await tester.pumpAndSettle();

      verify(() => mockAuth.verifyRecovery('tok-1', 'CODE123')).called(1);
      verify(() => mockAuth.resetPassword('tok-1', 'Pass!')).called(1);
    });

    testWidgets('CircularProgressIndicator appears while submit is pending', (tester) async {
      when(() => mockAuth.resetPassword(any(), any())).thenAnswer(
        (_) async => Future.delayed(const Duration(seconds: 2)),
      );

      await pumpApp(
        tester,
        const ResetPasswordScreen(token: 'tok-1'),
        overrides: _overrides(mockAuth),
      );
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField).at(2), 'Pass!');
      await tester.pump();

      await tester.drag(find.byType(ListView), const Offset(0, -500));
      await tester.pump();

      await tester.tap(find.byIcon(Icons.lock_reset_outlined));
      await tester.pump(); // first frame after tap: loading starts

      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      await tester.pump(const Duration(seconds: 3));
    });
  });
}
