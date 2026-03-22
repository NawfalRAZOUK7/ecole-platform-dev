/// Quiz domain entities — quiz, question, attempt, result.
///
/// Phase 10C: Maps to quiz engine API (from 9B backend).

class Quiz {
  final String id;
  final String title;
  final String? description;
  final String? subject;
  final String difficulty;
  final int? timeLimitMinutes;
  final int maxAttempts;
  final int questionCount;
  final int totalPoints;
  final String status;

  const Quiz({
    required this.id,
    required this.title,
    this.description,
    this.subject,
    required this.difficulty,
    this.timeLimitMinutes,
    required this.maxAttempts,
    required this.questionCount,
    required this.totalPoints,
    required this.status,
  });
}

class Question {
  final String id;
  final String questionType; // MCQ, TRUE_FALSE, FILL_IN, DRAG_DROP, MATCHING
  final String questionText;
  final String? questionMediaPath;
  final Map<String, dynamic>? options;
  final int points;
  final int order;

  const Question({
    required this.id,
    required this.questionType,
    required this.questionText,
    this.questionMediaPath,
    this.options,
    required this.points,
    required this.order,
  });
}

class QuizAttempt {
  final String id;
  final String quizId;
  final int attemptNo;
  final String? startedAt;
  final String? completedAt;
  final double? score;
  final double? maxScore;
  final String status;

  const QuizAttempt({
    required this.id,
    required this.quizId,
    required this.attemptNo,
    this.startedAt,
    this.completedAt,
    this.score,
    this.maxScore,
    required this.status,
  });
}

class QuizResultResponse {
  final String questionId;
  final String questionType;
  final String questionText;
  final dynamic studentAnswer;
  final dynamic correctAnswer;
  final bool? isCorrect;
  final double? pointsEarned;
  final int points;
  final String? explanation;

  const QuizResultResponse({
    required this.questionId,
    required this.questionType,
    required this.questionText,
    this.studentAnswer,
    this.correctAnswer,
    this.isCorrect,
    this.pointsEarned,
    required this.points,
    this.explanation,
  });
}

class AttemptResult {
  final QuizAttempt attempt;
  final List<QuizResultResponse> responses;

  const AttemptResult({
    required this.attempt,
    required this.responses,
  });
}

/// Content library item (extended from existing ContentItem for teacher browse).
class LibraryItem {
  final String id;
  final String? schoolId;
  final String title;
  final String contentType;
  final String? levelBand;
  final String? language;
  final String? subject;
  final String? description;
  final String origin; // platform / school
  final String status;

  const LibraryItem({
    required this.id,
    this.schoolId,
    required this.title,
    required this.contentType,
    this.levelBand,
    this.language,
    this.subject,
    this.description,
    required this.origin,
    required this.status,
  });
}

/// Teacher's content submission for platform review.
class ContentSubmission {
  final String id;
  final String contentItemId;
  final String contentTitle;
  final String status;
  final String? submittedAt;
  final String? reviewNotes;
  final String? promotedContentId;

  const ContentSubmission({
    required this.id,
    required this.contentItemId,
    required this.contentTitle,
    required this.status,
    this.submittedAt,
    this.reviewNotes,
    this.promotedContentId,
  });
}

/// Assigned content for a student's class.
class AssignedContent {
  final String id;
  final String contentItemId;
  final String title;
  final String contentType;
  final String? subject;
  final String? description;
  final String? progress; // not_started, started, completed
  final String? streamUrl;

  const AssignedContent({
    required this.id,
    required this.contentItemId,
    required this.title,
    required this.contentType,
    this.subject,
    this.description,
    this.progress,
    this.streamUrl,
  });
}

/// Quiz result for parent dashboard.
class QuizResultSummary {
  final String quizTitle;
  final int attemptNo;
  final double? score;
  final double? maxScore;
  final String status;
  final String? completedAt;

  const QuizResultSummary({
    required this.quizTitle,
    required this.attemptNo,
    this.score,
    this.maxScore,
    required this.status,
    this.completedAt,
  });
}
