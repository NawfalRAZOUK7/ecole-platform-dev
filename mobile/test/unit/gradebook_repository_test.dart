import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/repositories_impl/academic/gradebook_repository_impl.dart';
import 'package:ecole_platform/domain/entities/academic/gradebook.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

final _gridJson = {
  'class_id': 'cls-1',
  'class_name': 'CP-A',
  'columns': [
    {
      'assessment_id': 'a1',
      'title': 'Contrôle 1',
      'weight': 1.0,
      'max_score': 20.0,
      'date': '2026-03-10',
      'type': 'assessment',
    },
  ],
  'entries': [
    {
      'student_id': 'stu-1',
      'student_name': 'Alice',
      'grades': {'a1': 16.0},
      'weighted_average': 16.0,
    },
  ],
};

final _summaryJson = {
  'class_id': 'cls-1',
  'period_id': 'p1',
  'averages': [
    {'student_id': 'stu-1', 'avg': 15.5},
  ],
};

final _studentDetailJson = {
  'student_id': 'stu-1',
  'student_name': 'Alice',
  'class_id': 'cls-1',
  'class_name': 'CP-A',
  'weighted_average': 15.5,
  'assessments': [
    {
      'assessment_id': 'a1',
      'title': 'Contrôle 1',
      'type': 'assessment',
      'date': '2026-03-10',
      'max_score': 20.0,
      'weight': 1.0,
      'score': 15.5,
    },
  ],
};

final _transcriptJson = {
  'student_id': 'stu-1',
  'student_name': 'Alice',
  'periods': [
    {
      'period_id': 'p1',
      'label': 'Trimestre 1',
      'weighted_average': 15.0,
      'subjects': [
        {
          'subject_id': 'math',
          'subject_name': 'Mathématiques',
          'average': 16.0,
          'grades': <dynamic>[],
        },
      ],
    },
  ],
};

void main() {
  late MockApiClient api;
  late MockCacheStore cache;
  late GradebookRepositoryImpl repo;

  setUpAll(registerTestFallbacks);

  setUp(() {
    api = MockApiClient();
    cache = MockCacheStore();
    repo = GradebookRepositoryImpl(api: api, cache: cache);

    // Default cache: miss
    when(() => cache.get(any())).thenAnswer((_) async => null);
    when(() => cache.put(any(), any(), any())).thenAnswer((_) async {});
    when(() => cache.invalidate(any())).thenAnswer((_) async {});
    when(() => cache.invalidatePrefix(any())).thenAnswer((_) async {});
  });

  // ── getClassGradebook ─────────────────────────────────────────────────────

  group('getClassGradebook', () {
    test('fetches from API on cache miss and caches result', () async {
      when(() => api.get('/gradebook/classes/cls-1'))
          .thenAnswer((_) async => response(_gridJson));

      final result = await repo.getClassGradebook('cls-1');

      expect(result, isA<GradebookGrid>());
      expect(result.classId, 'cls-1');
      expect(result.columns, hasLength(1));
      expect(result.entries, hasLength(1));
      verify(() => cache.put(any(), any(), any())).called(1);
    });

    test('returns cached data without API call on cache hit', () async {
      when(() => cache.get('gradebook:grid:cls-1'))
          .thenAnswer((_) async => [_gridJson]);

      final result = await repo.getClassGradebook('cls-1');

      expect(result.classId, 'cls-1');
      verifyNever(() => api.get(any()));
    });

    test('propagates API error on miss', () async {
      when(() => api.get(any())).thenThrow(offlineError());

      expect(
        () => repo.getClassGradebook('cls-1'),
        throwsA(isA<ApiClientError>()),
      );
    });
  });

  // ── getStudentGrades ──────────────────────────────────────────────────────

  group('getStudentGrades', () {
    test('fetches student detail from API', () async {
      when(() => api.get('/gradebook/student/stu-1'))
          .thenAnswer((_) async => response(_studentDetailJson));

      final result = await repo.getStudentGrades('stu-1');

      expect(result, isA<StudentGradeDetail>());
      expect(result.studentId, 'stu-1');
      expect(result.weightedAverage, 15.5);
      expect(result.assessments, hasLength(1));
    });

    test('returns cached student detail on cache hit', () async {
      when(() => cache.get('gradebook:student:stu-1'))
          .thenAnswer((_) async => [_studentDetailJson]);

      final result = await repo.getStudentGrades('stu-1');

      expect(result.studentName, 'Alice');
      verifyNever(() => api.get(any()));
    });
  });

  // ── updateGrades ──────────────────────────────────────────────────────────

  group('updateGrades', () {
    test('posts bulk update and invalidates caches', () async {
      when(() => api.post('/gradebook/bulk-update', body: any(named: 'body')))
          .thenAnswer((_) async => response({}));

      const update = BulkGradeUpdate(
        classId: 'cls-1',
        grades: [
          GradeValueUpdate(
            studentId: 'stu-1',
            assessmentId: 'a1',
            value: 18.0,
          ),
        ],
      );
      await repo.updateGrades(update);

      final body = verify(
        () => api.post('/gradebook/bulk-update', body: captureAny(named: 'body')),
      ).captured.first as Map<String, dynamic>;
      expect(body['class_id'], 'cls-1');
      expect((body['grades'] as List).first['value'], 18.0);
      verify(() => cache.invalidate('gradebook:grid:cls-1')).called(1);
      verify(() => cache.invalidatePrefix('gradebook:summary:cls-1:')).called(1);
    });
  });

  // ── getWeightedSummary ────────────────────────────────────────────────────

  group('getWeightedSummary', () {
    test('fetches summary from API on miss', () async {
      when(
        () => api.get(
          '/gradebook/classes/cls-1/summary',
          params: any(named: 'params'),
        ),
      ).thenAnswer((_) async => response(_summaryJson));

      final result = await repo.getWeightedSummary('cls-1', periodId: 'p1');

      expect(result, isA<WeightedSummary>());
      expect(result.averages, hasLength(1));
      expect(result.averages.first.avg, 15.5);
    });

    test('fetches without period param when null', () async {
      when(
        () => api.get(
          '/gradebook/classes/cls-1/summary',
          params: any(named: 'params'),
        ),
      ).thenAnswer((_) async => response({...  _summaryJson, 'period_id': null}));

      await repo.getWeightedSummary('cls-1');

      final call = verify(
        () => api.get(
          '/gradebook/classes/cls-1/summary',
          params: captureAny(named: 'params'),
        ),
      ).captured.first;
      expect(call, isNull);
    });

    test('returns cached summary on hit', () async {
      when(() => cache.get('gradebook:summary:cls-1:p1'))
          .thenAnswer((_) async => [_summaryJson]);

      await repo.getWeightedSummary('cls-1', periodId: 'p1');

      verifyNever(() => api.get(any()));
    });
  });

  // ── exportGrades ──────────────────────────────────────────────────────────

  group('exportGrades', () {
    test('returns download_url from API response', () async {
      when(
        () => api.get(
          '/gradebook/classes/cls-1/export',
          params: any(named: 'params'),
        ),
      ).thenAnswer(
        (_) async => response({'download_url': 'https://cdn.example.com/grades.csv'}),
      );

      final url = await repo.exportGrades('cls-1');

      expect(url, 'https://cdn.example.com/grades.csv');
    });

    test('returns url field as fallback', () async {
      when(
        () => api.get(
          '/gradebook/classes/cls-1/export',
          params: any(named: 'params'),
        ),
      ).thenAnswer(
        (_) async => response({'url': 'https://cdn.example.com/grades.csv'}),
      );

      final url = await repo.exportGrades('cls-1');

      expect(url, 'https://cdn.example.com/grades.csv');
    });

    test('passes format param', () async {
      when(
        () => api.get(any(), params: any(named: 'params')),
      ).thenAnswer((_) async => response({'download_url': null}));

      await repo.exportGrades('cls-1', format: 'pdf');

      final params = verify(
        () => api.get(any(), params: captureAny(named: 'params')),
      ).captured.first as Map<String, dynamic>;
      expect(params['format'], 'pdf');
    });
  });

  // ── getCategories ─────────────────────────────────────────────────────────

  group('getCategories', () {
    test('returns list of category strings', () async {
      when(() => api.get('/gradebook/classes/cls-1/categories'))
          .thenAnswer(
        (_) async => response({'categories': ['Quiz', 'Exam', 'Homework']}),
      );

      final result = await repo.getCategories('cls-1');

      expect(result, ['Quiz', 'Exam', 'Homework']);
    });

    test('returns empty list when no categories', () async {
      when(() => api.get(any()))
          .thenAnswer((_) async => response({'categories': null}));

      final result = await repo.getCategories('cls-1');

      expect(result, isEmpty);
    });
  });

  // ── computeGrades ─────────────────────────────────────────────────────────

  group('computeGrades', () {
    test('posts compute request and returns summary', () async {
      when(
        () => api.post(
          '/gradebook/classes/cls-1/compute',
          body: any(named: 'body'),
        ),
      ).thenAnswer((_) async => response(_summaryJson));

      final result = await repo.computeGrades('cls-1', periodId: 'p1');

      expect(result, isA<WeightedSummary>());
      final body = verify(
        () => api.post(
          '/gradebook/classes/cls-1/compute',
          body: captureAny(named: 'body'),
        ),
      ).captured.first as Map<String, dynamic>;
      expect(body['period_id'], 'p1');
    });

    test('omits period_id when null', () async {
      when(
        () => api.post(any(), body: any(named: 'body')),
      ).thenAnswer((_) async => response(_summaryJson));

      await repo.computeGrades('cls-1');

      final body = verify(
        () => api.post(any(), body: captureAny(named: 'body')),
      ).captured.first as Map<String, dynamic>;
      expect(body.containsKey('period_id'), isFalse);
    });
  });

  // ── getTranscript ─────────────────────────────────────────────────────────

  group('getTranscript', () {
    test('fetches transcript from API', () async {
      when(() => api.get('/gradebook/transcript/stu-1'))
          .thenAnswer((_) async => response(_transcriptJson));

      final result = await repo.getTranscript('stu-1');

      expect(result, isA<GradeTranscript>());
      expect(result.studentId, 'stu-1');
      expect(result.periods, hasLength(1));
      expect(result.periods.first.subjects, hasLength(1));
    });

    test('returns cached transcript on hit', () async {
      when(() => cache.get('gradebook:transcript:stu-1'))
          .thenAnswer((_) async => [_transcriptJson]);

      final result = await repo.getTranscript('stu-1');

      expect(result.studentName, 'Alice');
      verifyNever(() => api.get(any()));
    });
  });
}
