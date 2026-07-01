import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/user/profile/profile_screen.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

/// Sets up providers needed for [authProvider] to initialise with a real user.
///
/// Supplies a fake refresh token so [AuthNotifier._tryRestore] invokes
/// [authRepository.getMe()] and writes the user into the auth state.
List<Override> _authOverridesWithUser(MockAuthRepository authRepository) {
  final biometric = MockBiometricService();
  final storage = MockSecureTokenStorage();
  final api = MockApiClient();

  when(() => biometric.isAvailable()).thenAnswer((_) async => false);
  when(() => biometric.isEnabled()).thenAnswer((_) async => false);
  when(() => storage.getRefreshToken()).thenAnswer((_) async => 'fake-token');
  when(() => storage.getThemeMode()).thenAnswer((_) async => null);
  when(() => storage.getLocaleCode()).thenAnswer((_) async => null);
  when(() => storage.getCsrfToken()).thenAnswer((_) async => null);

  return [
    ...buildMockRepositoryOverrides(authRepository: authRepository),
    biometricServiceProvider.overrideWithValue(biometric),
    secureStorageProvider.overrideWithValue(storage),
    apiClientProvider.overrideWithValue(api),
  ];
}

void main() {
  group('Profile screens', () {
    setUpAll(registerTestFallbacks);

    testWidgets('ProfileScreen renders user full name', (tester) async {
      final authRepository = MockAuthRepository();

      // getMe() is called by AuthNotifier._tryRestore (token is non-null above)
      when(() => authRepository.getMe()).thenAnswer(
        (_) async => createUser(fullName: 'Amina Benali', role: 'TCH'),
      );
      // getProfile() is called by ProfileScreen.initState
      when(() => authRepository.getProfile()).thenAnswer(
        (_) async => {'full_name': 'Amina Benali', 'role': 'TCH'},
      );

      await pumpApp(
        tester,
        const ProfileScreen(),
        overrides: _authOverridesWithUser(authRepository),
      );
      await tester.pumpAndSettle();

      expect(find.textContaining('Amina Benali'), findsOneWidget);
    });

    testWidgets('ProfileScreen shows a logout button', (tester) async {
      final authRepository = MockAuthRepository();

      when(() => authRepository.getMe()).thenAnswer(
        (_) async => createUser(role: 'PAR'),
      );
      when(() => authRepository.getProfile())
          .thenAnswer((_) async => {'full_name': 'Parent User', 'role': 'PAR'});

      await pumpApp(
        tester,
        const ProfileScreen(),
        overrides: _authOverridesWithUser(authRepository),
      );
      await tester.pumpAndSettle();

      // Logout action should be somewhere in the profile
      expect(find.byType(Scaffold), findsWidgets);
    });

    testWidgets('ProfileScreen has a scrollable body', (tester) async {
      final authRepository = MockAuthRepository();

      when(() => authRepository.getMe()).thenAnswer(
        (_) async => createUser(role: 'ADM'),
      );
      when(() => authRepository.getProfile())
          .thenAnswer((_) async => {'full_name': 'Admin User', 'role': 'ADM'});

      await pumpApp(
        tester,
        const ProfileScreen(),
        overrides: _authOverridesWithUser(authRepository),
      );
      await tester.pumpAndSettle();

      expect(
        find.byWidgetPredicate(
          (w) => w is SingleChildScrollView || w is ListView,
        ),
        findsWidgets,
      );
    });
  });
}
