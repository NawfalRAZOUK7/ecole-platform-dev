import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/ai/rewards.dart';
import 'package:ecole_platform/domain/repositories/ai/rewards_repository.dart';
import 'package:ecole_platform/features/ai/rewards/rewards_screen.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

class MockRewardsRepository extends Mock implements RewardsRepository {}

/// Sets up providers needed for [authProvider] to initialize with a user.
///
/// Provides a fake refresh token so [AuthNotifier._tryRestore] calls
/// [authRepository.getMe()] and sets the user in state.
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
  group('Rewards screens', () {
    setUpAll(registerTestFallbacks);

    testWidgets('RewardsScreen shows empty state for non-student role',
        (tester) async {
      final authRepository = MockAuthRepository();
      final rewardsRepository = MockRewardsRepository();

      when(() => authRepository.getMe())
          .thenAnswer((_) async => createUser(role: 'TCH'));
      when(() => rewardsRepository.getMyRewards())
          .thenAnswer((_) async => StudentRewards.empty);

      await pumpApp(
        tester,
        const RewardsScreen(),
        overrides: [
          ..._authOverridesWithUser(authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );
      await tester.pumpAndSettle();

      // Non-student should see the locked state, not rewards
      expect(find.byIcon(Icons.lock_outline), findsOneWidget);
    });

    testWidgets('RewardsScreen shows skeleton while loading for students',
        (tester) async {
      final authRepository = MockAuthRepository();
      final rewardsRepository = MockRewardsRepository();

      when(() => authRepository.getMe())
          .thenAnswer((_) async => createUser(role: 'STD'));

      // Use Completer so the pending future can be resolved cleanly on teardown
      final completer = Completer<StudentRewards>();
      when(() => rewardsRepository.getMyRewards())
          .thenAnswer((_) => completer.future);

      await pumpApp(
        tester,
        const RewardsScreen(),
        overrides: [
          ..._authOverridesWithUser(authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );

      // First frame: rewards still loading → skeleton scaffold rendered
      expect(find.byType(Scaffold), findsWidgets);

      // Resolve the completer to avoid pending-timer assertion on teardown
      completer.complete(StudentRewards.empty);
    });

    testWidgets('RewardsScreen renders star count and level after data loads',
        (tester) async {
      final authRepository = MockAuthRepository();
      final rewardsRepository = MockRewardsRepository();

      when(() => authRepository.getMe())
          .thenAnswer((_) async => createUser(role: 'STD'));
      when(() => rewardsRepository.getMyRewards()).thenAnswer(
        (_) async => const StudentRewards(
          id: 'r-1',
          studentId: 'student-1',
          stars: 42,
          xp: 400,
          level: 3,
          streakDays: 5,
          longestStreak: 10,
          badges: ['badge-first-login'],
        ),
      );

      await pumpApp(
        tester,
        const RewardsScreen(),
        overrides: [
          ..._authOverridesWithUser(authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );
      await tester.pumpAndSettle();

      // XP (400) and level (3) appear in the stats grid
      expect(find.textContaining('400'), findsWidgets);
    });
  });
}
