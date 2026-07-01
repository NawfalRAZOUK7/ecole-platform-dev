import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/domain/entities/lms/rubric.dart';
import 'package:ecole_platform/domain/repositories/lms/rubric_repository.dart';

RubricLevel _rubricLevelFromJson(Map<String, dynamic> json) {
  return RubricLevel(
    id: json['id'] as String? ?? '',
    label: json['label'] as String? ?? '',
    score: (json['score'] as num?)?.toDouble() ?? 0,
    description: json['description'] as String? ?? '',
  );
}

RubricCriterion _rubricCriterionFromJson(Map<String, dynamic> json) {
  return RubricCriterion(
    id: json['id'] as String? ?? '',
    name: json['name'] as String? ?? '',
    weight: (json['weight'] as num?)?.toDouble() ?? 0,
    levels: (json['levels'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(_rubricLevelFromJson)
        .toList(),
  );
}

Rubric _rubricFromJson(Map<String, dynamic> json) {
  return Rubric(
    id: json['id'] as String? ?? '',
    title: json['title'] as String? ?? '',
    description: json['description'] as String?,
    subject: json['subject'] as String?,
    criteria: (json['criteria'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(_rubricCriterionFromJson)
        .toList(),
    maxScore: (json['max_score'] as num?)?.toDouble() ?? 0,
    createdBy: json['created_by'] as String? ?? '',
    createdAt: json['created_at'] as String? ?? '',
    updatedAt: json['updated_at'] as String? ?? '',
  );
}

RubricGradeEntry _rubricGradeEntryFromJson(Map<String, dynamic> json) {
  return RubricGradeEntry(
    studentId: json['student_id'] as String? ?? '',
    criterionId: json['criterion_id'] as String? ?? '',
    levelId: json['level_id'] as String? ?? '',
    score: (json['score'] as num?)?.toDouble() ??
        (json['points_awarded'] as num?)?.toDouble() ??
        0,
  );
}

RubricGradeResult _rubricGradeResultFromJson(Map<String, dynamic> json) {
  return RubricGradeResult(
    studentId: json['student_id'] as String? ?? '',
    rubricId: json['rubric_id'] as String? ?? '',
    totalScore: (json['total_score'] as num?)?.toDouble() ?? 0,
    maxScore: (json['max_score'] as num?)?.toDouble() ?? 0,
    percentage: (json['percentage'] as num?)?.toDouble() ?? 0,
    entries: (json['entries'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(_rubricGradeEntryFromJson)
        .toList(),
  );
}

RubricResultsResponse _rubricResultsResponseFromJson(
  Map<String, dynamic> json,
) {
  return RubricResultsResponse(
    rubricId: json['rubric_id'] as String? ?? '',
    results: (json['results'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>()
        .map(_rubricGradeResultFromJson)
        .toList(),
  );
}

class RubricRepositoryImpl implements RubricRepository {
  final ApiClient _api;

  RubricRepositoryImpl({required ApiClient api}) : _api = api;

  Map<String, dynamic> _criterionToJson(RubricCriterion criterion) {
    return {
      'name': criterion.name,
      'weight': criterion.weight,
      'levels': criterion.levels
          .map(
            (level) => {
              'label': level.label,
              'score': level.score,
              'description': level.description,
            },
          )
          .toList(),
    };
  }

  @override
  Future<List<Rubric>> listRubrics() async {
    final response = await _api.list('/rubrics');
    return response.data.map(_rubricFromJson).toList();
  }

  @override
  Future<Rubric> getRubric(String id) async {
    final response = await _api.get('/rubrics/$id');
    return _rubricFromJson(response.data);
  }

  @override
  Future<Rubric> createRubric({
    required String title,
    String? description,
    String? subject,
    required List<RubricCriterion> criteria,
  }) async {
    final response = await _api.post(
      '/rubrics',
      body: {
        'title': title,
        'description': description,
        'subject': subject,
        'criteria': criteria.map(_criterionToJson).toList(),
      },
    );
    return _rubricFromJson(response.data);
  }

  @override
  Future<Rubric> updateRubric({
    required String id,
    required String title,
    String? description,
    String? subject,
    required List<RubricCriterion> criteria,
  }) async {
    final response = await _api.put(
      '/rubrics/$id',
      body: {
        'id': id,
        'title': title,
        'description': description,
        'subject': subject,
        'criteria': criteria.map(_criterionToJson).toList(),
      },
    );
    return _rubricFromJson(response.data);
  }

  @override
  Future<Rubric> duplicateRubric(String id) async {
    final response = await _api.post('/rubrics/$id/duplicate', body: {});
    return _rubricFromJson(response.data);
  }

  @override
  Future<RubricGradeResult> gradeRubric({
    required String rubricId,
    String? assignmentId,
    required List<RubricGradeEntry> entries,
  }) async {
    await _api.post(
      '/submissions/${assignmentId ?? rubricId}/grade-rubric',
      body: entries
          .map(
            (entry) => {
              'criterion_id': entry.criterionId,
              'level_id': entry.levelId,
              'points_awarded': entry.score,
              'comment': null,
            },
          )
          .toList(),
    );

    final totalScore =
        entries.fold<double>(0, (sum, entry) => sum + entry.score);
    return RubricGradeResult(
      studentId: entries.firstOrNull?.studentId ?? '',
      rubricId: rubricId,
      totalScore: totalScore,
      maxScore: totalScore,
      percentage: 100,
      entries: entries,
    );
  }

  @override
  Future<RubricResultsResponse> getRubricResults(String rubricId) async {
    final response = await _api.get('/submissions/$rubricId/rubric-results');
    return _rubricResultsResponseFromJson(response.data);
  }
}
