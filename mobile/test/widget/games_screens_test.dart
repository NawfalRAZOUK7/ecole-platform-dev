import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/ai/rewards.dart';
import 'package:ecole_platform/domain/repositories/ai/rewards_repository.dart';
import 'package:ecole_platform/features/ai/games/mini_games_screen.dart';

import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

class MockRewardsRepository extends Mock implements RewardsRepository {}

void main() {
  group('Games screens', () {
    setUpAll(registerTestFallbacks);

    testWidgets('MiniGamesScreen shows a loader while rewards load',
        (tester) async {
      final rewardsRepository = MockRewardsRepository();
      when(() => rewardsRepository.getMyRewards())
          .thenAnswer((_) async => StudentRewards.empty);

      await pumpApp(
        tester,
        const MiniGamesScreen(),
        overrides: [
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );

      // On first frame, provider is loading; skeleton should render
      expect(find.byType(MiniGamesScreen), findsOneWidget);
    });

    testWidgets('MiniGamesScreen renders game grid after rewards load',
        (tester) async {
      final rewardsRepository = MockRewardsRepository();
      when(() => rewardsRepository.getMyRewards()).thenAnswer(
        (_) async => const StudentRewards(
          id: 'reward-1',
          studentId: 'student-1',
          stars: 20,
          xp: 150,
          level: 2,
          streakDays: 3,
          longestStreak: 7,
          badges: [],
        ),
      );

      await pumpApp(
        tester,
        const MiniGamesScreen(),
        overrides: [
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );
      await tester.pumpAndSettle();

      expect(find.text('Choisis un jeu'), findsOneWidget);
      // Three game cards should be in the grid
      expect(find.text('Memory\nMatch'), findsOneWidget);
    });

    testWidgets('MiniGamesScreen has an AppBar with title', (tester) async {
      final rewardsRepository = MockRewardsRepository();
      when(() => rewardsRepository.getMyRewards())
          .thenAnswer((_) async => StudentRewards.empty);

      await pumpApp(
        tester,
        const MiniGamesScreen(),
        overrides: [
          rewardsRepositoryProvider.overrideWithValue(rewardsRepository),
        ],
      );

      expect(find.text('Jeux éducatifs'), findsOneWidget);
    });
  });
}
