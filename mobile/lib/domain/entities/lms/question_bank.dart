class QuestionBankChoice {
  final String id;
  final String text;
  final bool isCorrect;

  const QuestionBankChoice({
    required this.id,
    required this.text,
    required this.isCorrect,
  });
}

class QuestionBankQuestion {
  final String id;
  final String subject;
  final String type;
  final String difficulty;
  final String text;
  final List<QuestionBankChoice> choices;
  final String? correctAnswer;
  final List<String> tags;
  final String createdBy;
  final String createdAt;

  const QuestionBankQuestion({
    required this.id,
    required this.subject,
    required this.type,
    required this.difficulty,
    required this.text,
    required this.choices,
    this.correctAnswer,
    required this.tags,
    required this.createdBy,
    required this.createdAt,
  });
}

class QuestionBankImportResult {
  final int imported;
  final int skipped;
  final List<QuestionBankQuestion> questions;

  const QuestionBankImportResult({
    required this.imported,
    required this.skipped,
    required this.questions,
  });
}

class GeneratedQuestionQuiz {
  final List<QuestionBankQuestion> questions;
  final int total;

  const GeneratedQuestionQuiz({
    required this.questions,
    required this.total,
  });
}

class QuestionBankStats {
  final int total;
  final Map<String, int> bySubject;
  final Map<String, int> byType;
  final Map<String, int> byDifficulty;

  const QuestionBankStats({
    required this.total,
    required this.bySubject,
    required this.byType,
    required this.byDifficulty,
  });
}
