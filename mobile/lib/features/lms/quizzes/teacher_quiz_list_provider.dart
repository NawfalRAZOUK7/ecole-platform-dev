/// Teacher-facing quiz list provider (read-only + publish toggle).
///
/// Phase I (Web/Mobile parity) — I7.
///
/// Backs `teacher_quiz_list_screen.dart`. Fetches `GET /quizzes` (no server-
/// side filters — we filter client-side for the small seeded dataset),
/// supports publish/unpublish via `POST /quizzes/{id}/publish`.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';

enum TeacherQuizFilter { all, published, draft }

class TeacherQuizSummary {
  final String id;
  final String title;
  final String? description;
  final String? subject;
  final String? levelBand;
  final String? difficulty;
  final String status; // draft | published | archived
  final int questionCount;
  final int totalPoints;
  final int? timeLimitMinutes;
  final int maxAttempts;

  const TeacherQuizSummary({
    required this.id,
    required this.title,
    required this.description,
    required this.subject,
    required this.levelBand,
    required this.difficulty,
    required this.status,
    required this.questionCount,
    required this.totalPoints,
    required this.timeLimitMinutes,
    required this.maxAttempts,
  });

  bool get isPublished => status.toLowerCase() == 'published';
  bool get isDraft => status.toLowerCase() == 'draft';

  TeacherQuizSummary copyWith({String? status}) => TeacherQuizSummary(
        id: id,
        title: title,
        description: description,
        subject: subject,
        levelBand: levelBand,
        difficulty: difficulty,
        status: status ?? this.status,
        questionCount: questionCount,
        totalPoints: totalPoints,
        timeLimitMinutes: timeLimitMinutes,
        maxAttempts: maxAttempts,
      );

  factory TeacherQuizSummary.fromJson(Map<String, dynamic> json) {
    return TeacherQuizSummary(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      description: json['description'] as String?,
      subject: json['subject'] as String?,
      levelBand: json['level_band'] as String?,
      difficulty: json['difficulty'] as String?,
      status: json['status'] as String? ?? 'draft',
      questionCount: (json['question_count'] as num?)?.toInt() ?? 0,
      totalPoints: (json['total_points'] as num?)?.toInt() ?? 0,
      timeLimitMinutes: (json['time_limit_minutes'] as num?)?.toInt(),
      maxAttempts: (json['max_attempts'] as num?)?.toInt() ?? 1,
    );
  }
}

class TeacherQuizListState {
  final List<TeacherQuizSummary> quizzes;
  final TeacherQuizFilter filter;
  final String searchQuery;

  const TeacherQuizListState({
    required this.quizzes,
    required this.filter,
    required this.searchQuery,
  });

  List<TeacherQuizSummary> get visibleQuizzes {
    final q = searchQuery.trim().toLowerCase();
    return quizzes.where((quiz) {
      switch (filter) {
        case TeacherQuizFilter.all:
          break;
        case TeacherQuizFilter.published:
          if (!quiz.isPublished) return false;
          break;
        case TeacherQuizFilter.draft:
          if (!quiz.isDraft) return false;
          break;
      }
      if (q.isEmpty) return true;
      return quiz.title.toLowerCase().contains(q) ||
          (quiz.subject?.toLowerCase().contains(q) ?? false);
    }).toList(growable: false);
  }

  TeacherQuizListState copyWith({
    List<TeacherQuizSummary>? quizzes,
    TeacherQuizFilter? filter,
    String? searchQuery,
  }) =>
      TeacherQuizListState(
        quizzes: quizzes ?? this.quizzes,
        filter: filter ?? this.filter,
        searchQuery: searchQuery ?? this.searchQuery,
      );
}

class TeacherQuizListNotifier extends AsyncNotifier<TeacherQuizListState> {
  @override
  Future<TeacherQuizListState> build() async {
    final quizzes = await _fetch();
    return TeacherQuizListState(
      quizzes: quizzes,
      filter: TeacherQuizFilter.all,
      searchQuery: '',
    );
  }

  Future<List<TeacherQuizSummary>> _fetch() async {
    final api = ref.read(apiClientProvider);
    final resp = await api.list('/quizzes', params: {'limit': '100'});
    return resp.data.map(TeacherQuizSummary.fromJson).toList(growable: false);
  }

  Future<void> refresh() async {
    final current = state.value;
    state = await AsyncValue.guard(() async {
      final quizzes = await _fetch();
      return (current ??
              const TeacherQuizListState(
                quizzes: [],
                filter: TeacherQuizFilter.all,
                searchQuery: '',
              ))
          .copyWith(quizzes: quizzes);
    });
  }

  void setFilter(TeacherQuizFilter filter) {
    final current = state.value;
    if (current == null) return;
    state = AsyncData(current.copyWith(filter: filter));
  }

  void setSearchQuery(String query) {
    final current = state.value;
    if (current == null) return;
    state = AsyncData(current.copyWith(searchQuery: query));
  }

  Future<void> togglePublish(TeacherQuizSummary quiz) async {
    final current = state.value;
    if (current == null) return;

    // Optimistic update.
    final nextStatus = quiz.isPublished ? 'draft' : 'published';
    final optimistic = current.quizzes
        .map((q) => q.id == quiz.id ? q.copyWith(status: nextStatus) : q)
        .toList(growable: false);
    state = AsyncData(current.copyWith(quizzes: optimistic));

    final api = ref.read(apiClientProvider);
    try {
      if (quiz.isPublished) {
        // No unpublish endpoint exists → PUT status back to draft.
        await api.put('/quizzes/${quiz.id}', body: {'status': 'draft'});
      } else {
        await api.post('/quizzes/${quiz.id}/publish');
      }
      await refresh();
    } catch (_) {
      // Roll back on failure.
      state = AsyncData(current);
      rethrow;
    }
  }
}

final teacherQuizListProvider =
    AsyncNotifierProvider<TeacherQuizListNotifier, TeacherQuizListState>(
  TeacherQuizListNotifier.new,
);
