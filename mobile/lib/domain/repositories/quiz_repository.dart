/// Quiz repository interface — domain layer contract.
///
/// Phase 10C: Quiz engine for student quiz player + teacher quiz manager.
import '../entities/quiz.dart';
import 'feed_repository.dart'; // for PaginatedList

abstract class QuizRepository {
  /// List available quizzes for the student.
  Future<List<Quiz>> getQuizzes();

  /// Get quiz detail with questions.
  Future<Quiz> getQuiz(String quizId);

  /// Get questions for a quiz.
  Future<List<Question>> getQuizQuestions(String quizId);

  /// Start a quiz attempt.
  Future<QuizAttempt> startAttempt(String quizId);

  /// Submit a response to a question within an attempt.
  Future<void> submitResponse(String attemptId, {
    required String questionId,
    required dynamic answer,
  });

  /// Finalize and submit the attempt.
  Future<void> submitAttempt(String attemptId);

  /// Get results for a completed attempt.
  Future<AttemptResult> getAttemptResults(String attemptId);

  /// Get quiz results for parent dashboard.
  Future<List<QuizResultSummary>> getQuizResults();

  /// Cache quiz questions locally for offline use.
  Future<void> cacheQuizForOffline(String quizId, List<Question> questions);

  /// Get cached quiz questions (offline fallback).
  Future<List<Question>?> getCachedQuestions(String quizId);
}
