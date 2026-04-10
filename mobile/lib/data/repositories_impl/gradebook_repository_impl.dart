import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/domain/entities/gradebook.dart';
import 'package:ecole_platform/domain/repositories/gradebook_repository.dart';

class GradebookRepositoryImpl implements GradebookRepository {
  final ApiClient _api;
  final CacheStore _cache;

  GradebookRepositoryImpl({
    required ApiClient api,
    required CacheStore cache,
  })  : _api = api,
        _cache = cache;

  @override
  Future<GradebookGrid> getClassGradebook(String classId) async {
    final cacheKey = 'gradebook:grid:$classId';
    final cached = await _getCachedObject(cacheKey);
    if (cached != null) {
      return _gridFromJson(cached);
    }

    final response = await _api.get('/gradebook/classes/$classId');
    await _putCachedObject(cacheKey, response.data, CacheTtl.gradebook);
    return _gridFromJson(response.data);
  }

  @override
  Future<StudentGradeDetail> getStudentGrades(String studentId) async {
    final cacheKey = 'gradebook:student:$studentId';
    final cached = await _getCachedObject(cacheKey);
    if (cached != null) {
      return _studentDetailFromJson(cached);
    }

    final response = await _api.get('/gradebook/student/$studentId');
    await _putCachedObject(cacheKey, response.data, CacheTtl.gradebook);
    return _studentDetailFromJson(response.data);
  }

  @override
  Future<void> updateGrades(BulkGradeUpdate update) async {
    await _api.post(
      '/gradebook/bulk-update',
      body: {
        'class_id': update.classId,
        'grades': update.grades
            .map(
              (grade) => {
                'student_id': grade.studentId,
                'assessment_id': grade.assessmentId,
                'value': grade.value,
              },
            )
            .toList(),
      },
    );
    await _cache.invalidate('gradebook:grid:${update.classId}');
    await _cache.invalidatePrefix('gradebook:summary:${update.classId}:');
  }

  @override
  Future<WeightedSummary> getWeightedSummary(
    String classId, {
    String? periodId,
  }) async {
    final cacheKey = 'gradebook:summary:$classId:${periodId ?? 'all'}';
    final cached = await _getCachedObject(cacheKey);
    if (cached != null) {
      return _summaryFromJson(cached);
    }

    final response = await _api.get(
      '/gradebook/classes/$classId/summary',
      params: periodId == null ? null : {'period_id': periodId},
    );
    await _putCachedObject(cacheKey, response.data, CacheTtl.gradebook);
    return _summaryFromJson(response.data);
  }

  @override
  Future<String?> exportGrades(String classId, {String format = 'csv'}) async {
    final response = await _api.get(
      '/gradebook/classes/$classId/export',
      params: {'format': format},
    );
    return response.data['download_url'] as String? ??
        response.data['url'] as String?;
  }

  @override
  Future<List<String>> getCategories(String classId) async {
    final response = await _api.get('/gradebook/classes/$classId/categories');
    final items = response.data['categories'] as List<dynamic>? ?? const [];
    return items.map((item) => item.toString()).toList();
  }

  @override
  Future<WeightedSummary> computeGrades(
    String classId, {
    String? periodId,
  }) async {
    final response = await _api.post(
      '/gradebook/classes/$classId/compute',
      body: {
        if (periodId != null) 'period_id': periodId,
      },
    );
    return _summaryFromJson(response.data);
  }

  @override
  Future<GradeTranscript> getTranscript(String studentId) async {
    final cacheKey = 'gradebook:transcript:$studentId';
    final cached = await _getCachedObject(cacheKey);
    if (cached != null) {
      return _transcriptFromJson(cached);
    }

    final response = await _api.get('/gradebook/transcript/$studentId');
    await _putCachedObject(cacheKey, response.data, CacheTtl.gradebook);
    return _transcriptFromJson(response.data);
  }

  Future<Map<String, dynamic>?> _getCachedObject(String cacheKey) async {
    final cached = await _cache.get(cacheKey);
    if (cached == null || cached.isEmpty) {
      return null;
    }
    return cached.first;
  }

  Future<void> _putCachedObject(
    String cacheKey,
    Map<String, dynamic> payload,
    int ttl,
  ) async {
    await _cache.put(cacheKey, [payload], ttl);
  }

  GradebookGrid _gridFromJson(Map<String, dynamic> json) {
    final columns = (json['columns'] as List<dynamic>? ?? const [])
        .map((column) => _columnFromJson(column as Map<String, dynamic>))
        .toList();
    final entries = (json['entries'] as List<dynamic>? ?? const [])
        .map((entry) => _entryFromJson(entry as Map<String, dynamic>))
        .toList();

    return GradebookGrid(
      classId: json['class_id'] as String? ?? '',
      className: json['class_name'] as String? ?? '',
      columns: columns,
      entries: entries,
    );
  }

  GradebookColumn _columnFromJson(Map<String, dynamic> json) {
    return GradebookColumn(
      assessmentId: json['assessment_id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      weight: (json['weight'] as num?)?.toDouble() ?? 0,
      maxScore: (json['max_score'] as num?)?.toDouble() ?? 20,
      date: json['date'] as String? ?? '',
      type: json['type'] as String? ?? 'assessment',
    );
  }

  GradebookEntry _entryFromJson(Map<String, dynamic> json) {
    final grades = (json['grades'] as Map<String, dynamic>? ?? const {})
        .map(
          (key, value) => MapEntry(
            key,
            value == null ? null : (value as num).toDouble(),
          ),
        );

    return GradebookEntry(
      studentId: json['student_id'] as String? ?? '',
      studentName: json['student_name'] as String? ?? '',
      grades: grades,
      weightedAverage: (json['weighted_average'] as num?)?.toDouble() ?? 0,
    );
  }

  StudentGradeDetail _studentDetailFromJson(Map<String, dynamic> json) {
    return StudentGradeDetail(
      studentId: json['student_id'] as String? ?? '',
      studentName: json['student_name'] as String? ?? '',
      classId: json['class_id'] as String? ?? '',
      className: json['class_name'] as String? ?? '',
      weightedAverage: (json['weighted_average'] as num?)?.toDouble() ?? 0,
      assessments: (json['assessments'] as List<dynamic>? ?? const [])
          .map(
            (assessment) =>
                _assessmentFromJson(assessment as Map<String, dynamic>),
          )
          .toList(),
    );
  }

  StudentAssessmentGrade _assessmentFromJson(Map<String, dynamic> json) {
    return StudentAssessmentGrade(
      assessmentId: json['assessment_id'] as String? ?? '',
      title: json['title'] as String? ?? '',
      type: json['type'] as String? ?? 'assessment',
      date: json['date'] as String? ?? '',
      maxScore: (json['max_score'] as num?)?.toDouble() ?? 20,
      weight: (json['weight'] as num?)?.toDouble() ?? 0,
      score: (json['score'] as num?)?.toDouble(),
    );
  }

  WeightedSummary _summaryFromJson(Map<String, dynamic> json) {
    return WeightedSummary(
      classId: json['class_id'] as String? ?? '',
      periodId: json['period_id'] as String?,
      averages: (json['averages'] as List<dynamic>? ?? const [])
          .map(
            (average) => WeightedAverageItem(
              studentId:
                  (average as Map<String, dynamic>)['student_id'] as String? ??
                      '',
              avg: (average['avg'] as num?)?.toDouble() ?? 0,
            ),
          )
          .toList(),
    );
  }

  GradeTranscript _transcriptFromJson(Map<String, dynamic> json) {
    return GradeTranscript(
      studentId: json['student_id'] as String? ?? '',
      studentName: json['student_name'] as String? ?? '',
      periods: (json['periods'] as List<dynamic>? ?? const [])
          .map(
            (period) => TranscriptPeriod(
              periodId:
                  (period as Map<String, dynamic>)['period_id'] as String? ??
                      '',
              label: period['label'] as String? ?? '',
              weightedAverage:
                  (period['weighted_average'] as num?)?.toDouble() ?? 0,
              subjects: (period['subjects'] as List<dynamic>? ?? const [])
                  .map(
                    (subject) => TranscriptSubject(
                      subjectId:
                          (subject as Map<String, dynamic>)['subject_id']
                                  as String? ??
                              '',
                      subjectName: subject['subject_name'] as String? ?? '',
                      average: (subject['average'] as num?)?.toDouble() ?? 0,
                      grades: (subject['grades'] as List<dynamic>? ?? const [])
                          .map(
                            (grade) => _assessmentFromJson(
                              grade as Map<String, dynamic>,
                            ),
                          )
                          .toList(),
                    ),
                  )
                  .toList(),
            ),
          )
          .toList(),
    );
  }
}
