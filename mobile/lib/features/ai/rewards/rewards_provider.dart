library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/ai/rewards.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';

class RewardsNotifier extends AsyncNotifier<StudentRewards> {
  @override
  Future<StudentRewards> build() {
    return ref.read(rewardsRepositoryProvider).getMyRewards();
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(rewardsRepositoryProvider).getMyRewards(),
    );
  }

  Future<void> awardEvent({
    required String eventType,
    int starsEarned = 0,
    int xpEarned = 0,
    String? sourceType,
    String? sourceId,
  }) async {
    final studentId = ref.read(authProvider).user?.id;
    if (studentId == null || studentId.isEmpty) {
      return;
    }

    final previousState = state;
    try {
      final updated = await ref.read(rewardsRepositoryProvider).award(
            studentId: studentId,
            eventType: eventType,
            stars: starsEarned,
            xp: xpEarned,
            sourceType: sourceType,
            sourceId: sourceId,
          );
      state = AsyncData(updated);
    } catch (_) {
      state = previousState;
    }
  }

  Future<void> awardStoryComplete(String contentItemId) => awardEvent(
        eventType: 'content_completed',
        starsEarned: 3,
        xpEarned: 50,
        sourceType: 'content',
        sourceId: contentItemId,
      );

  Future<void> awardQuizPass(String quizId) => awardEvent(
        eventType: 'quiz_passed',
        starsEarned: 2,
        xpEarned: 30,
        sourceType: 'quiz',
        sourceId: quizId,
      );

  Future<void> awardMiniGameComplete(String gameId) => awardEvent(
        eventType: 'game_completed',
        starsEarned: 1,
        xpEarned: 20,
        sourceType: 'game',
        sourceId: gameId,
      );
}

final rewardsProvider =
    AsyncNotifierProvider<RewardsNotifier, StudentRewards>(RewardsNotifier.new);
