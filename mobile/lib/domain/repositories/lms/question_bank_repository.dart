import 'package:ecole_platform/domain/entities/lms/question_bank.dart';

abstract class QuestionBankRepository {
  Future<QuestionBankQuestion> createQuestion({
    required String subject,
    required String type,
    required String difficulty,
    required String text,
    List<Map<String, dynamic>> choices = const [],
    String? correctAnswer,
    List<String> tags = const [],
  });

  Future<List<QuestionBankQuestion>> listQuestions({
    String? subject,
    String? type,
    String? difficulty,
  });

  Future<QuestionBankImportResult> importFromQuiz(String quizId);

  Future<GeneratedQuestionQuiz> generateQuiz({
    required String subject,
    String? difficulty,
    required int count,
    List<String> tags = const [],
  });

  Future<QuestionBankStats> getStats();
}
