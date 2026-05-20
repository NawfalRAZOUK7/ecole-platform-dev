/// Quiz analytics providers — teacher/admin-facing.
///
/// Phase I (Web/Mobile parity) — I6.
///
/// Two `FutureProvider.family` providers, keyed by `quizId`:
///   * [quizAnalyticsProvider] — aggregate stats + per-question accuracy
///     (GET /quizzes/{quizId}/analytics).
///   * [quizAttemptsProvider]  — recent attempts list (student, score, date)
///     (GET /quizzes/{quizId}/attempts?limit=50).
///
/// Matches the web `QuizAnalyticsPage` data shape so we can mirror UI.
library;

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';

/// Per-question accuracy breakdown.
class QuizQuestionStats {
  final String questionId;
  final String questionText;
  final String questionType;
  final int totalResponses;
  final int correctResponses;
  final double? accuracy; // percent [0-100] or null if no responses

  const QuizQuestionStats({
    required this.questionId,
    required this.questionText,
    required this.questionType,
    required this.totalResponses,
    required this.correctResponses,
    required this.accuracy,
  });

  factory QuizQuestionStats.fromJson(Map<String, dynamic> json) {
    return QuizQuestionStats(
      questionId: json['question_id'] as String? ?? '',
      questionText: json['question_text'] as String? ?? '',
      questionType: json['question_type'] as String? ?? 'mcq',
      totalResponses: (json['total_responses'] as num?)?.toInt() ?? 0,
      correctResponses: (json['correct_responses'] as num?)?.toInt() ?? 0,
      accuracy: (json['accuracy'] as num?)?.toDouble(),
    );
  }
}

/// Aggregate quiz analytics payload.
class QuizAnalytics {
  final String quizId;
  final String title;
  final int totalAttempts;
  final int completedAttempts;
  final double? averageScore;
  final double? maxScoreAchieved;
  final double? minScoreAchieved;
  final double? averagePercentage;
  final List<QuizQuestionStats> questionStats;

  const QuizAnalytics({
    required this.quizId,
    required this.title,
    required this.totalAttempts,
    required this.completedAttempts,
    required this.averageScore,
    required this.maxScoreAchieved,
    required this.minScoreAchieved,
    required this.averagePercentage,
    required this.questionStats,
  });

  double get completionRate =>
      totalAttempts == 0 ? 0 : completedAttempts / totalAttempts * 100;

  factory QuizAnalytics.fromJson(Map<String, dynamic> json) {
    final questionsJson = (json['question_stats'] as List<dynamic>? ?? [])
        .cast<Map<String, dynamic>>();
    return QuizAnalytics(
      quizId: json['quiz_id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      totalAttempts: (json['total_attempts'] as num?)?.toInt() ?? 0,
      completedAttempts: (json['completed_attempts'] as num?)?.toInt() ?? 0,
      averageScore: (json['average_score'] as num?)?.toDouble(),
      maxScoreAchieved: (json['max_score_achieved'] as num?)?.toDouble(),
      minScoreAchieved: (json['min_score_achieved'] as num?)?.toDouble(),
      averagePercentage: (json['average_percentage'] as num?)?.toDouble(),
      questionStats:
          questionsJson.map(QuizQuestionStats.fromJson).toList(growable: false),
    );
  }
}

/// A single quiz attempt (teacher view).
class QuizAttemptEntry {
  final String id;
  final String studentId;
  final String studentName;
  final int attemptNo;
  final String? startedAt;
  final String? completedAt;
  final double? score;
  final int maxScore;
  final double? percentage;
  final String status;

  const QuizAttemptEntry({
    required this.id,
    required this.studentId,
    required this.studentName,
    required this.attemptNo,
    required this.startedAt,
    required this.completedAt,
    required this.score,
    required this.maxScore,
    required this.percentage,
    required this.status,
  });

  factory QuizAttemptEntry.fromJson(Map<String, dynamic> json) {
    return QuizAttemptEntry(
      id: json['id'] as String? ?? '',
      studentId: json['student_id'] as String? ?? '',
      studentName: json['student_name'] as String? ?? '',
      attemptNo: (json['attempt_no'] as num?)?.toInt() ?? 1,
      startedAt: json['started_at'] as String?,
      completedAt: json['completed_at'] as String?,
      score: (json['score'] as num?)?.toDouble(),
      maxScore: (json['max_score'] as num?)?.toInt() ?? 0,
      percentage: (json['percentage'] as num?)?.toDouble(),
      status: json['status'] as String? ?? 'STARTED',
    );
  }
}

final quizAnalyticsProvider = FutureProvider.autoDispose
    .family<QuizAnalytics, String>((ref, quizId) async {
  final api = ref.read(apiClientProvider);
  final resp = await api.get('/quizzes/$quizId/analytics');
  return QuizAnalytics.fromJson(resp.data);
});

final quizAttemptsProvider = FutureProvider.autoDispose
    .family<List<QuizAttemptEntry>, String>((ref, quizId) async {
  final api = ref.read(apiClientProvider);
  final resp = await api.list(
    '/quizzes/$quizId/attempts',
    params: {'limit': '50'},
  );
  return resp.data.map(QuizAttemptEntry.fromJson).toList(growable: false);
});
