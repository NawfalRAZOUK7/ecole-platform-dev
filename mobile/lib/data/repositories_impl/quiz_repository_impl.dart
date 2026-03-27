/// Quiz repository implementation — API calls + offline cache.
///
/// Phase 10C: Quiz engine for student quiz player.

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/domain/entities/quiz.dart';
import 'package:ecole_platform/domain/repositories/quiz_repository.dart';

Quiz _quizFromJson(Map<String, dynamic> json) {
  return Quiz(
    id: json['id'] as String,
    title: json['title'] as String,
    description: json['description'] as String?,
    subject: json['subject'] as String?,
    difficulty: json['difficulty'] as String? ?? 'medium',
    timeLimitMinutes: json['time_limit_minutes'] as int?,
    maxAttempts: json['max_attempts'] as int? ?? 1,
    questionCount: json['question_count'] as int? ?? 0,
    totalPoints: json['total_points'] as int? ?? 0,
    status: json['status'] as String? ?? 'published',
  );
}

Question _questionFromJson(Map<String, dynamic> json) {
  return Question(
    id: json['id'] as String,
    questionType: json['question_type'] as String,
    questionText: json['question_text'] as String,
    questionMediaPath: json['question_media_path'] as String?,
    options: json['options'] as Map<String, dynamic>?,
    points: json['points'] as int? ?? 1,
    order: json['order'] as int? ?? 0,
  );
}

QuizAttempt _attemptFromJson(Map<String, dynamic> json) {
  return QuizAttempt(
    id: json['id'] as String,
    quizId: json['quiz_id'] as String,
    attemptNo: json['attempt_no'] as int? ?? 1,
    startedAt: json['started_at'] as String?,
    completedAt: json['completed_at'] as String?,
    score: (json['score'] as num?)?.toDouble(),
    maxScore: (json['max_score'] as num?)?.toDouble(),
    status: json['status'] as String? ?? 'in_progress',
  );
}

QuizResultResponse _resultResponseFromJson(Map<String, dynamic> json) {
  return QuizResultResponse(
    questionId: json['question_id'] as String,
    questionType: json['question_type'] as String,
    questionText: json['question_text'] as String,
    studentAnswer: json['student_answer'],
    correctAnswer: json['correct_answer'],
    isCorrect: json['is_correct'] as bool?,
    pointsEarned: (json['points_earned'] as num?)?.toDouble(),
    points: json['points'] as int? ?? 1,
    explanation: json['explanation'] as String?,
  );
}

QuizResultSummary _quizResultSummaryFromJson(Map<String, dynamic> json) {
  return QuizResultSummary(
    quizTitle: json['quiz_title'] as String? ?? '',
    attemptNo: json['attempt_no'] as int? ?? 1,
    score: (json['score'] as num?)?.toDouble(),
    maxScore: (json['max_score'] as num?)?.toDouble(),
    status: json['status'] as String? ?? 'completed',
    completedAt: json['completed_at'] as String?,
  );
}

class QuizRepositoryImpl implements QuizRepository {
  final ApiClient _api;
  final CacheStore _cache;

  QuizRepositoryImpl({required ApiClient api, required CacheStore cache})
      : _api = api,
        _cache = cache;

  @override
  Future<List<Quiz>> getQuizzes() async {
    final resp = await _api.list('/quizzes', params: {'status': 'published'});
    return resp.data.map(_quizFromJson).toList();
  }

  @override
  Future<Quiz> getQuiz(String quizId) async {
    final resp = await _api.get('/quizzes/$quizId');
    return _quizFromJson(resp.data);
  }

  @override
  Future<List<Question>> getQuizQuestions(String quizId) async {
    final resp = await _api.get('/quizzes/$quizId');
    final questionsJson = resp.data['questions'] as List<dynamic>? ?? [];
    return questionsJson
        .map((q) => _questionFromJson(q as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<QuizAttempt> startAttempt(String quizId) async {
    final resp = await _api.post('/quizzes/$quizId/start');
    return _attemptFromJson(resp.data);
  }

  @override
  Future<void> submitResponse(
    String attemptId, {
    required String questionId,
    required dynamic answer,
  }) async {
    await _api.post('/attempts/$attemptId/respond', body: {
      'question_id': questionId,
      'answer': answer,
    });
  }

  @override
  Future<void> submitAttempt(String attemptId) async {
    await _api.post('/attempts/$attemptId/submit');
  }

  @override
  Future<AttemptResult> getAttemptResults(String attemptId) async {
    final resp = await _api.get('/attempts/$attemptId/results');
    final attemptJson = resp.data['attempt'] as Map<String, dynamic>;
    final responsesJson = resp.data['responses'] as List<dynamic>? ?? [];

    return AttemptResult(
      attempt: _attemptFromJson(attemptJson),
      responses: responsesJson
          .map((r) => _resultResponseFromJson(r as Map<String, dynamic>))
          .toList(),
    );
  }

  @override
  Future<List<QuizResultSummary>> getQuizResults() async {
    try {
      final resp = await _api.list('/results/quizzes');
      return resp.data.map(_quizResultSummaryFromJson).toList();
    } catch (_) {
      return [];
    }
  }

  @override
  Future<void> cacheQuizForOffline(
      String quizId, List<Question> questions) async {
    final data = questions
        .map((q) => {
              'id': q.id,
              'question_type': q.questionType,
              'question_text': q.questionText,
              'question_media_path': q.questionMediaPath,
              'options': q.options,
              'points': q.points,
              'order': q.order,
            })
        .toList();
    await _cache.put('quiz_offline:$quizId', data, 7 * 24 * 3600); // 7 days
  }

  @override
  Future<List<Question>?> getCachedQuestions(String quizId) async {
    final cached = await _cache.get('quiz_offline:$quizId');
    if (cached == null) return null;
    return cached.map(_questionFromJson).toList();
  }
}
