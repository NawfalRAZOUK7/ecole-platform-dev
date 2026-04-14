/// Riverpod provider for the student rewards (Stars / XP) system.
///
/// Fetches from GET /rewards/me and exposes helpers for triggering reward
/// events (story completion, quiz pass, streak, etc.).
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';

// ---------------------------------------------------------------------------
// Data model
// ---------------------------------------------------------------------------

class StudentRewards {
  final String id;
  final int stars;
  final int xp;
  final int level;
  final int streakDays;
  final int longestStreak;
  final List<String> badges;

  const StudentRewards({
    required this.id,
    required this.stars,
    required this.xp,
    required this.level,
    required this.streakDays,
    required this.longestStreak,
    required this.badges,
  });

  factory StudentRewards.fromJson(Map<String, dynamic> json) => StudentRewards(
        id: json['id'] as String,
        stars: (json['stars'] as num?)?.toInt() ?? 0,
        xp: (json['xp'] as num?)?.toInt() ?? 0,
        level: (json['level'] as num?)?.toInt() ?? 1,
        streakDays: (json['streak_days'] as num?)?.toInt() ?? 0,
        longestStreak: (json['longest_streak'] as num?)?.toInt() ?? 0,
        badges: List<String>.from(json['badges'] as List? ?? []),
      );

  static const empty = StudentRewards(
    id: '',
    stars: 0,
    xp: 0,
    level: 1,
    streakDays: 0,
    longestStreak: 0,
    badges: [],
  );

  StudentRewards copyWith({
    int? stars,
    int? xp,
    int? level,
    int? streakDays,
    int? longestStreak,
    List<String>? badges,
  }) =>
      StudentRewards(
        id: id,
        stars: stars ?? this.stars,
        xp: xp ?? this.xp,
        level: level ?? this.level,
        streakDays: streakDays ?? this.streakDays,
        longestStreak: longestStreak ?? this.longestStreak,
        badges: badges ?? this.badges,
      );

  int get xpForNextLevel => level * 100;
  double get xpProgress =>
      xp > 0 ? (xp % xpForNextLevel) / xpForNextLevel : 0.0;
}

// ---------------------------------------------------------------------------
// Notifier
// ---------------------------------------------------------------------------

class RewardsNotifier extends AsyncNotifier<StudentRewards> {
  @override
  Future<StudentRewards> build() => _fetch();

  Future<StudentRewards> _fetch() async {
    try {
      final api = ref.read(apiClientProvider);
      final resp = await api.get('/rewards/me');
      return StudentRewards.fromJson(resp.data);
    } catch (_) {
      return StudentRewards.empty;
    }
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(_fetch);
  }

  /// Award a reward event (called after story completion, quiz, etc.).
  /// Optimistically updates local stars/XP then re-fetches.
  Future<void> awardEvent({
    required String eventType,
    int starsEarned = 0,
    int xpEarned = 0,
    String? sourceType,
    String? sourceId,
  }) async {
    final api = ref.read(apiClientProvider);
    try {
      await api.post('/rewards/award', body: {
        'event_type': eventType,
        'stars_earned': starsEarned,
        'xp_earned': xpEarned,
        if (sourceType != null) 'source_type': sourceType,
        if (sourceId != null) 'source_id': sourceId,
      });
      // Refresh authoritative state from server
      await refresh();
    } catch (_) {
      // Non-blocking — reward failure shouldn't break the UX
    }
  }

  /// Convenience: award story completion (3 stars, 50 XP).
  Future<void> awardStoryComplete(String contentItemId) => awardEvent(
        eventType: 'story_complete',
        starsEarned: 3,
        xpEarned: 50,
        sourceType: 'content_item',
        sourceId: contentItemId,
      );

  /// Convenience: award quiz pass (2 stars, 30 XP).
  Future<void> awardQuizPass(String quizId) => awardEvent(
        eventType: 'quiz_pass',
        starsEarned: 2,
        xpEarned: 30,
        sourceType: 'quiz',
        sourceId: quizId,
      );

  /// Convenience: award mini-game complete (1 star, 20 XP).
  Future<void> awardMiniGameComplete(String gameId) => awardEvent(
        eventType: 'mini_game_complete',
        starsEarned: 1,
        xpEarned: 20,
        sourceType: 'mini_game',
        sourceId: gameId,
      );
}

final rewardsProvider =
    AsyncNotifierProvider<RewardsNotifier, StudentRewards>(RewardsNotifier.new);
