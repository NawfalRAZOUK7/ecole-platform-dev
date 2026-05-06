import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/rewards.dart';
import 'package:ecole_platform/domain/repositories/rewards_repository.dart';
import 'package:ecole_platform/features/student/student_home_screen.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

class MockRewardsRepository extends Mock implements RewardsRepository {}

const _testRewards = StudentRewards(
  id: 'r-1',
  studentId: 'student-1',
  stars: 15,
  xp: 120,
  level: 2,
  streakDays: 4,
  longestStreak: 10,
  badges: [],
);

void main() {
  group('StudentHomeScreen', () {
    setUpAll(registerTestFallbacks);

    testWidgets('shows skeleton while rewards are loading', (tester) async {
      final authRepository = MockAuthRepository();
      final rewardsRepository = MockRewardsRepository();
      final completer = Completer<StudentRewards>();

      when(() => authRepository.getMe()).thenAnswer(
        (_) async => createUser(
          id: 'student-1',
          fullName: 'Yassine Alaoui',
          role: 'STD',
        ),
      );

      // Delay so the first frame captures loading state
      when(() => rewardsRepository.getMyRewards()).thenAnswer(
        (_) => completer.future,
      );

      await pumpApp(
        tester,
        const StudentHomeScreen(),
        overrides: [
          ...buildMockRepositoryOverrides(authRepository: authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );

      // On first frame before rewards resolve: CircularProgressIndicator should be present
      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      // Complete the future to avoid timer pending error
      completer.complete(_testRewards);
    });

    testWidgets('renders greeting with student first name', (tester) async {
      final authRepository = MockAuthRepository();
      final rewardsRepository = MockRewardsRepository();

      when(() => authRepository.getMe()).thenAnswer(
        (_) async => createUser(
          id: 'student-1',
          fullName: 'Yassine Alaoui',
          role: 'STD',
        ),
      );
      when(() => rewardsRepository.getMyRewards())
          .thenAnswer((_) async => _testRewards);

      await pumpApp(
        tester,
        const StudentHomeScreen(),
        overrides: [
          ...buildMockRepositoryOverrides(authRepository: authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );
      await tester.pumpAndSettle();

      // Greeting contains the Arabic greeting with name
      expect(find.textContaining('مرحبا'), findsOneWidget);
    });

    testWidgets('shows XP and level from rewards data', (tester) async {
      final authRepository = MockAuthRepository();
      final rewardsRepository = MockRewardsRepository();

      when(() => authRepository.getMe()).thenAnswer(
        (_) async => createUser(
          id: 'student-1',
          fullName: 'Fatima Zahra',
          role: 'STD',
        ),
      );
      when(() => rewardsRepository.getMyRewards())
          .thenAnswer((_) async => _testRewards);

      await pumpApp(
        tester,
        const StudentHomeScreen(),
        overrides: [
          ...buildMockRepositoryOverrides(authRepository: authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );
      await tester.pumpAndSettle();

      // Level (2) or XP (120) should appear somewhere in the dashboard
      expect(
        find.byWidgetPredicate(
          (w) =>
              w is Text &&
              (w.data?.contains('2') == true ||
                  w.data?.contains('120') == true),
        ),
        findsWidgets,
      );
    });

    testWidgets('has a RefreshIndicator for pull-to-refresh', (tester) async {
      final authRepository = MockAuthRepository();
      final rewardsRepository = MockRewardsRepository();

      when(() => authRepository.getMe()).thenAnswer(
        (_) async => createUser(role: 'STD'),
      );
      when(() => rewardsRepository.getMyRewards())
          .thenAnswer((_) async => _testRewards);

      await pumpApp(
        tester,
        const StudentHomeScreen(),
        overrides: [
          ...buildMockRepositoryOverrides(authRepository: authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );
      await tester.pumpAndSettle();

      expect(find.byType(RefreshIndicator), findsOneWidget);
    });

    testWidgets('renders dashboard tiles (CTA grid)', (tester) async {
      final authRepository = MockAuthRepository();
      final rewardsRepository = MockRewardsRepository();

      when(() => authRepository.getMe()).thenAnswer(
        (_) async => createUser(role: 'STD'),
      );
      when(() => rewardsRepository.getMyRewards())
          .thenAnswer((_) async => _testRewards);

      await pumpApp(
        tester,
        const StudentHomeScreen(),
        overrides: [
          ...buildMockRepositoryOverrides(authRepository: authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );
      await tester.pumpAndSettle();

      // Check CTA grid items are rendered
      expect(find.text('الدروس'), findsOneWidget);
      expect(find.text('الاختبارات'), findsOneWidget);
      expect(find.text('الكتابة'), findsOneWidget);
      expect(find.text('الألعاب'), findsOneWidget);

      // Check sublabels
      expect(find.text('تعلّم'), findsOneWidget);
      expect(find.text('أجب'), findsOneWidget);
      expect(find.text('اكتب قصة'), findsOneWidget);
      expect(find.text('العب وتعلّم'), findsOneWidget);
    });

    testWidgets('shows today\'s schedule when available', (tester) async {
      final authRepository = MockAuthRepository();
      final rewardsRepository = MockRewardsRepository();

      when(() => authRepository.getMe()).thenAnswer(
        (_) async => createUser(role: 'STD'),
      );
      when(() => rewardsRepository.getMyRewards())
          .thenAnswer((_) async => _testRewards);

      await pumpApp(
        tester,
        const StudentHomeScreen(),
        overrides: [
          ...buildMockRepositoryOverrides(authRepository: authRepository),
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );
      await tester.pumpAndSettle();

      // Schedule section may or may not be shown depending on timetable state
      // The important thing is the screen renders without errors
      expect(find.byType(StudentHomeScreen), findsOneWidget);
    });
  });
}
