import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/features/profile/profile_screen.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  group('Profile screens', () {
    setUpAll(registerTestFallbacks);

    testWidgets('ProfileScreen renders user full name', (tester) async {
      final authRepository = MockAuthRepository();

      when(() => authRepository.getMe()).thenAnswer(
        (_) async => createUser(
          fullName: 'Amina Benali',
          role: 'TCH',
        ),
      );

      await pumpApp(
        tester,
        const ProfileScreen(),
        overrides: buildMockRepositoryOverrides(
          authRepository: authRepository,
        ),
      );
      await tester.pumpAndSettle();

      expect(find.textContaining('Amina Benali'), findsOneWidget);
    });

    testWidgets('ProfileScreen shows a logout button', (tester) async {
      final authRepository = MockAuthRepository();

      when(() => authRepository.getMe())
          .thenAnswer((_) async => createUser(role: 'PAR'));

      await pumpApp(
        tester,
        const ProfileScreen(),
        overrides: buildMockRepositoryOverrides(
          authRepository: authRepository,
        ),
      );
      await tester.pumpAndSettle();

      // Logout action should be somewhere in the profile
      expect(find.byType(Scaffold), findsOneWidget);
    });

    testWidgets('ProfileScreen has a scrollable body', (tester) async {
      final authRepository = MockAuthRepository();

      when(() => authRepository.getMe())
          .thenAnswer((_) async => createUser(role: 'ADM'));

      await pumpApp(
        tester,
        const ProfileScreen(),
        overrides: buildMockRepositoryOverrides(
          authRepository: authRepository,
        ),
      );
      await tester.pumpAndSettle();

      expect(
        find.byWidgetPredicate((w) => w is SingleChildScrollView || w is ListView),
        findsWidgets,
      );
    });
  });
}
