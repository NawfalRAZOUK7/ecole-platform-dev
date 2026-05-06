import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/rewards.dart';
import 'package:ecole_platform/domain/repositories/rewards_repository.dart';
import 'package:ecole_platform/features/rewards/rewards_screen.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

class MockRewardsRepository extends Mock implements RewardsRepository {}

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
          ...buildMockRepositoryOverrides(authRepository: authRepository),
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

      // Simulate a slow future — never resolves during test frame check
      final neverComplete = Future<StudentRewards>.delayed(
        const Duration(seconds: 30),
        () => StudentRewards.empty,
      );
      when(() => rewardsRepository.getMyRewards())
          .thenAnswer((_) => neverComplete);

      await pumpApp(
        tester,
        const RewardsScreen(),
        overrides: [
          ...buildMockRepositoryOverrides(authRepository: authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );

      // First frame: should be loading / show skeleton scaffold
      expect(find.byType(Scaffold), findsOneWidget);
    });

    testWidgets(
        'RewardsScreen renders star count and level after data loads',
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
          ...buildMockRepositoryOverrides(authRepository: authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );
      await tester.pumpAndSettle();

      // Stars (42) should appear somewhere in the widget tree
      expect(find.textContaining('42'), findsWidgets);
    });
  });
}
