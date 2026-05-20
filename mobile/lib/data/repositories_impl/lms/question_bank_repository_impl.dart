import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/domain/entities/lms/question_bank.dart';
import 'package:ecole_platform/domain/repositories/lms/question_bank_repository.dart';

QuestionBankChoice _questionBankChoiceFromJson(Map<String, dynamic> json) {
  return QuestionBankChoice(
    id: json['id'] as String? ?? '',
    text: json['text'] as String? ?? '',
    isCorrect: json['is_correct'] as bool? ?? false,
  );
}

QuestionBankQuestion _questionBankQuestionFromJson(Map<String, dynamic> json) {
  return QuestionBankQuestion(
    id: json['id'] as String? ?? '',
    subject: json['subject'] as String? ?? '',
    type: json['type'] as String? ?? 'mcq',
    difficulty: json['difficulty'] as String? ?? 'medium',
    text: json['text'] as String? ?? '',
    choices: (json['choices'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(_questionBankChoiceFromJson)
        .toList(),
    correctAnswer: json['correct_answer'] as String?,
    tags: (json['tags'] as List<dynamic>? ?? const [])
        .map((item) => item.toString())
        .toList(),
    createdBy: json['created_by'] as String? ?? '',
    createdAt: json['created_at'] as String? ?? '',
  );
}

QuestionBankImportResult _questionBankImportResultFromJson(
  Map<String, dynamic> json,
) {
  return QuestionBankImportResult(
    imported: json['imported'] as int? ?? 0,
    skipped: json['skipped'] as int? ?? 0,
    questions: (json['questions'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(_questionBankQuestionFromJson)
        .toList(),
  );
}

GeneratedQuestionQuiz _generatedQuestionQuizFromJson(
  Map<String, dynamic> json,
) {
  return GeneratedQuestionQuiz(
    questions: (json['questions'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(_questionBankQuestionFromJson)
        .toList(),
    total: json['total'] as int? ?? 0,
  );
}

QuestionBankStats _questionBankStatsFromJson(Map<String, dynamic> json) {
  Map<String, int> parseCounts(String key) {
    final counts = <String, int>{};
    final data = json[key] as Map<String, dynamic>? ?? const {};
    for (final entry in data.entries) {
      counts[entry.key] = (entry.value as num?)?.toInt() ?? 0;
    }
    return counts;
  }

  return QuestionBankStats(
    total: json['total'] as int? ?? 0,
    bySubject: parseCounts('by_subject'),
    byType: parseCounts('by_type'),
    byDifficulty: parseCounts('by_difficulty'),
  );
}

class QuestionBankRepositoryImpl implements QuestionBankRepository {
  final ApiClient _api;

  QuestionBankRepositoryImpl({required ApiClient api}) : _api = api;

  @override
  Future<QuestionBankQuestion> createQuestion({
    required String subject,
    required String type,
    required String difficulty,
    required String text,
    List<Map<String, dynamic>> choices = const [],
    String? correctAnswer,
    List<String> tags = const [],
  }) async {
    final response = await _api.post(
      '/question-bank',
      body: {
        'subject': subject,
        'type': type,
        'difficulty': difficulty,
        'text': text,
        'choices': choices,
        'correct_answer': correctAnswer,
        'tags': tags,
      },
    );
    return _questionBankQuestionFromJson(response.data);
  }

  @override
  Future<List<QuestionBankQuestion>> listQuestions({
    String? subject,
    String? type,
    String? difficulty,
  }) async {
    final params = <String, dynamic>{};
    if (subject != null && subject.isNotEmpty) params['subject'] = subject;
    if (type != null && type.isNotEmpty) params['type'] = type;
    if (difficulty != null && difficulty.isNotEmpty) {
      params['difficulty'] = difficulty;
    }

    final response = await _api.list('/question-bank', params: params);
    return response.data.map(_questionBankQuestionFromJson).toList();
  }

  @override
  Future<QuestionBankImportResult> importFromQuiz(String quizId) async {
    final response = await _api.post('/question-bank/import/$quizId', body: {});
    return _questionBankImportResultFromJson(response.data);
  }

  @override
  Future<GeneratedQuestionQuiz> generateQuiz({
    required String subject,
    String? difficulty,
    required int count,
    List<String> tags = const [],
  }) async {
    final response = await _api.post(
      '/question-bank/generate-quiz',
      body: {
        'subject': subject,
        'difficulty': difficulty,
        'count': count,
        'tags': tags,
      },
    );
    return _generatedQuestionQuizFromJson(response.data);
  }

  @override
  Future<QuestionBankStats> getStats() async {
    final response = await _api.get('/question-bank/stats');
    return _questionBankStatsFromJson(response.data);
  }
}
