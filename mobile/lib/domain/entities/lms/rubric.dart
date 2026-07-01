class RubricLevel {
  final String id;
  final String label;
  final double score;
  final String description;

  const RubricLevel({
    required this.id,
    required this.label,
    required this.score,
    required this.description,
  });
}

class RubricCriterion {
  final String id;
  final String name;
  final double weight;
  final List<RubricLevel> levels;

  const RubricCriterion({
    required this.id,
    required this.name,
    required this.weight,
    required this.levels,
  });
}

class Rubric {
  final String id;
  final String title;
  final String? description;
  final String? subject;
  final List<RubricCriterion> criteria;
  final double maxScore;
  final String createdBy;
  final String createdAt;
  final String updatedAt;

  const Rubric({
    required this.id,
    required this.title,
    this.description,
    this.subject,
    required this.criteria,
    required this.maxScore,
    required this.createdBy,
    required this.createdAt,
    required this.updatedAt,
  });
}

class RubricGradeEntry {
  final String studentId;
  final String criterionId;
  final String levelId;
  final double score;

  const RubricGradeEntry({
    required this.studentId,
    required this.criterionId,
    required this.levelId,
    required this.score,
  });
}

class RubricGradeResult {
  final String studentId;
  final String rubricId;
  final double totalScore;
  final double maxScore;
  final double percentage;
  final List<RubricGradeEntry> entries;

  const RubricGradeResult({
    required this.studentId,
    required this.rubricId,
    required this.totalScore,
    required this.maxScore,
    required this.percentage,
    required this.entries,
  });
}

class RubricResultsResponse {
  final String rubricId;
  final List<RubricGradeResult> results;

  const RubricResultsResponse({
    required this.rubricId,
    required this.results,
  });
}
