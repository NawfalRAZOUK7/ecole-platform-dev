class SkillDimension {
  final String id;
  final String title;
  final String description;
  final bool isActive;

  const SkillDimension({
    required this.id,
    required this.title,
    required this.description,
    required this.isActive,
  });

  factory SkillDimension.fromJson(Map<String, dynamic> json) {
    return SkillDimension(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? json['name']?.toString() ?? '',
      description: json['description']?.toString() ?? '',
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}

class SkillMilestone {
  final String id;
  final String dimensionId;
  final String title;
  final String level;
  final bool isActive;

  const SkillMilestone({
    required this.id,
    required this.dimensionId,
    required this.title,
    required this.level,
    required this.isActive,
  });

  factory SkillMilestone.fromJson(Map<String, dynamic> json) {
    return SkillMilestone(
      id: json['id']?.toString() ?? '',
      dimensionId: json['dimension_id']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      level: json['level']?.toString() ?? '',
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}

class SkillScoreItem {
  final String id;
  final String label;
  final double score;

  const SkillScoreItem({
    required this.id,
    required this.label,
    required this.score,
  });

  factory SkillScoreItem.fromJson(Map<String, dynamic> json) {
    return SkillScoreItem(
      id: json['id']?.toString() ?? json['dimension_id']?.toString() ?? '',
      label: json['label']?.toString() ??
          json['dimension_name']?.toString() ??
          json['title']?.toString() ??
          '',
      score: (json['score'] as num?)?.toDouble() ??
          (json['value'] as num?)?.toDouble() ??
          (json['progress'] as num?)?.toDouble() ??
          0,
    );
  }
}

class SkillProgressItem {
  final String dimensionId;
  final String dimensionName;
  final double score;
  final String levelLabel;

  const SkillProgressItem({
    required this.dimensionId,
    required this.dimensionName,
    required this.score,
    required this.levelLabel,
  });

  factory SkillProgressItem.fromJson(Map<String, dynamic> json) {
    return SkillProgressItem(
      dimensionId: json['dimension_id']?.toString() ?? '',
      dimensionName: json['dimension_name']?.toString() ?? '',
      score: (json['score'] as num?)?.toDouble() ??
          (json['progress_rate'] as num?)?.toDouble() ??
          0,
      levelLabel: json['level_label']?.toString() ??
          json['milestone_label']?.toString() ??
          '',
    );
  }
}

class SkillEvaluation {
  final String studentId;
  final double overallScore;
  final String summary;
  final List<SkillScoreItem> dimensions;

  const SkillEvaluation({
    required this.studentId,
    required this.overallScore,
    required this.summary,
    required this.dimensions,
  });

  factory SkillEvaluation.fromJson(Map<String, dynamic> json) {
    final dimensionsJson =
        (json['dimensions'] as List<dynamic>? ?? const []).cast<Map<String, dynamic>>();
    return SkillEvaluation(
      studentId: json['student_id']?.toString() ?? '',
      overallScore: (json['overall_score'] as num?)?.toDouble() ?? 0,
      summary: json['summary']?.toString() ?? '',
      dimensions: dimensionsJson.map(SkillScoreItem.fromJson).toList(),
    );
  }
}

class SkillPassport {
  final String studentId;
  final String studentName;
  final String academicYearId;
  final double overallScore;
  final String? issuedAt;
  final List<SkillScoreItem> dimensions;

  const SkillPassport({
    required this.studentId,
    required this.studentName,
    required this.academicYearId,
    required this.overallScore,
    required this.dimensions,
    this.issuedAt,
  });

  factory SkillPassport.fromJson(Map<String, dynamic> json) {
    final dimensionsJson =
        (json['dimensions'] as List<dynamic>? ?? const []).cast<Map<String, dynamic>>();
    return SkillPassport(
      studentId: json['student_id']?.toString() ?? '',
      studentName: json['student_name']?.toString() ?? '',
      academicYearId: json['academic_year_id']?.toString() ?? '',
      overallScore: (json['overall_score'] as num?)?.toDouble() ?? 0,
      issuedAt: json['issued_at']?.toString(),
      dimensions: dimensionsJson.map(SkillScoreItem.fromJson).toList(),
    );
  }
}

class SkillClassAnalytics {
  final String classId;
  final double averageScore;
  final int studentCount;
  final List<SkillScoreItem> dimensions;

  const SkillClassAnalytics({
    required this.classId,
    required this.averageScore,
    required this.studentCount,
    required this.dimensions,
  });

  factory SkillClassAnalytics.fromJson(Map<String, dynamic> json) {
    final dimensionsJson =
        (json['dimensions'] as List<dynamic>? ?? const []).cast<Map<String, dynamic>>();
    return SkillClassAnalytics(
      classId: json['class_id']?.toString() ?? '',
      averageScore: (json['average_score'] as num?)?.toDouble() ?? 0,
      studentCount: (json['student_count'] as num?)?.toInt() ?? 0,
      dimensions: dimensionsJson.map(SkillScoreItem.fromJson).toList(),
    );
  }
}

class SkillSchoolAnalytics {
  final double overallScore;
  final List<SkillScoreItem> dimensions;

  const SkillSchoolAnalytics({
    required this.overallScore,
    required this.dimensions,
  });

  factory SkillSchoolAnalytics.fromJson(Map<String, dynamic> json) {
    final dimensionsJson =
        (json['dimensions'] as List<dynamic>? ?? const []).cast<Map<String, dynamic>>();
    return SkillSchoolAnalytics(
      overallScore: (json['overall_score'] as num?)?.toDouble() ??
          (json['average_score'] as num?)?.toDouble() ??
          0,
      dimensions: dimensionsJson.map(SkillScoreItem.fromJson).toList(),
    );
  }
}

class SkillLeaderboardEntry {
  final String studentId;
  final String studentName;
  final double score;

  const SkillLeaderboardEntry({
    required this.studentId,
    required this.studentName,
    required this.score,
  });

  factory SkillLeaderboardEntry.fromJson(Map<String, dynamic> json) {
    return SkillLeaderboardEntry(
      studentId: json['student_id']?.toString() ?? '',
      studentName: json['student_name']?.toString() ?? '',
      score: (json['score'] as num?)?.toDouble() ?? 0,
    );
  }
}

class SkillAnalyticsBundle {
  final SkillClassAnalytics analytics;
  final List<SkillLeaderboardEntry> leaderboard;

  const SkillAnalyticsBundle({
    required this.analytics,
    required this.leaderboard,
  });
}
