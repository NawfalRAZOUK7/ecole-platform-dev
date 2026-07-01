/// Result entity — student grade/assignment result.
///
/// Maps to GET /results response (ResultResponse schema).
class Result {
  final String assignmentId;
  final String assignmentTitle;
  final String courseTitle;
  final String? submissionId;
  final String? status;
  final double? score;
  final String? feedbackText;
  final int totalPoints;
  final String? dueAt;

  const Result({
    required this.assignmentId,
    required this.assignmentTitle,
    required this.courseTitle,
    this.submissionId,
    this.status,
    this.score,
    this.feedbackText,
    required this.totalPoints,
    this.dueAt,
  });
}
