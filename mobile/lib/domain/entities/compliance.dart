class MenCurriculum {
  final String id;
  final String title;
  final String subject;
  final String? level;
  final String? grade;

  const MenCurriculum({
    required this.id,
    required this.title,
    required this.subject,
    this.level,
    this.grade,
  });

  factory MenCurriculum.fromJson(Map<String, dynamic> json) {
    return MenCurriculum(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? json['name']?.toString() ?? '',
      subject: json['subject']?.toString() ?? '',
      level: json['level']?.toString(),
      grade: json['grade']?.toString(),
    );
  }
}

class MenObjective {
  final String id;
  final String curriculumId;
  final String title;
  final int? trimester;

  const MenObjective({
    required this.id,
    required this.curriculumId,
    required this.title,
    this.trimester,
  });

  factory MenObjective.fromJson(Map<String, dynamic> json) {
    return MenObjective(
      id: json['id']?.toString() ?? '',
      curriculumId: json['curriculum_id']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      trimester: (json['trimester'] as num?)?.toInt(),
    );
  }
}

class CurriculumMapping {
  final String id;
  final String curriculumId;
  final String? objectiveId;
  final String? courseId;
  final String? contentItemId;

  const CurriculumMapping({
    required this.id,
    required this.curriculumId,
    this.objectiveId,
    this.courseId,
    this.contentItemId,
  });

  factory CurriculumMapping.fromJson(Map<String, dynamic> json) {
    return CurriculumMapping(
      id: json['id']?.toString() ?? '',
      curriculumId: json['curriculum_id']?.toString() ?? '',
      objectiveId: json['objective_id']?.toString(),
      courseId: json['course_id']?.toString(),
      contentItemId: json['content_item_id']?.toString(),
    );
  }
}

class ComplianceMetric {
  final String label;
  final double value;

  const ComplianceMetric({
    required this.label,
    required this.value,
  });

  factory ComplianceMetric.fromJson(Map<String, dynamic> json) {
    return ComplianceMetric(
      label: json['label']?.toString() ?? '',
      value: (json['value'] as num?)?.toDouble() ?? 0,
    );
  }
}

class ComplianceDashboardData {
  final double coverageRate;
  final double objectivesCoveredRate;
  final double missingCoverageRate;
  final List<ComplianceMetric> metrics;

  const ComplianceDashboardData({
    required this.coverageRate,
    required this.objectivesCoveredRate,
    required this.missingCoverageRate,
    required this.metrics,
  });

  factory ComplianceDashboardData.fromJson(Map<String, dynamic> json) {
    final metricsJson = (json['metrics'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>();
    return ComplianceDashboardData(
      coverageRate: (json['coverage_rate'] as num?)?.toDouble() ??
          (json['coverage'] as num?)?.toDouble() ??
          0,
      objectivesCoveredRate:
          (json['objectives_covered_rate'] as num?)?.toDouble() ??
              (json['objectives_rate'] as num?)?.toDouble() ??
              0,
      missingCoverageRate:
          (json['missing_coverage_rate'] as num?)?.toDouble() ??
              (json['missing_rate'] as num?)?.toDouble() ??
              0,
      metrics: metricsJson.map(ComplianceMetric.fromJson).toList(),
    );
  }
}

class ComplianceReport {
  final String id;
  final String title;
  final String status;
  final String? createdAt;
  final String? downloadUrl;

  const ComplianceReport({
    required this.id,
    required this.title,
    required this.status,
    this.createdAt,
    this.downloadUrl,
  });

  factory ComplianceReport.fromJson(Map<String, dynamic> json) {
    return ComplianceReport(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? json['name']?.toString() ?? '',
      status: json['status']?.toString() ?? 'pending',
      createdAt: json['created_at']?.toString(),
      downloadUrl: json['download_url']?.toString(),
    );
  }
}
