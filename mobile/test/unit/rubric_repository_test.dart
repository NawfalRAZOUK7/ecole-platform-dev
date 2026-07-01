import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/repositories_impl/lms/rubric_repository_impl.dart';
import 'package:ecole_platform/domain/entities/lms/rubric.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

Map<String, dynamic> _rubricJson({
  String id = 'rub-1',
  String title = 'Grille orale',
}) =>
    {
      'id': id,
      'title': title,
      'description': 'Grille pour évaluation orale',
      'subject': 'Français',
      'max_score': 20.0,
      'created_by': 'teacher-1',
      'created_at': '2026-01-01T00:00:00Z',
      'updated_at': '2026-01-01T00:00:00Z',
      'criteria': [
        {
          'id': 'crit-1',
          'name': 'Prononciation',
          'weight': 0.4,
          'levels': [
            {
              'id': 'lvl-1',
              'label': 'Excellent',
              'score': 8.0,
              'description': '',
            },
            {'id': 'lvl-2', 'label': 'Bien', 'score': 5.0, 'description': ''},
          ],
        },
      ],
    };

Map<String, dynamic> _rubricResultsJson() => {
      'rubric_id': 'rub-1',
      'results': <dynamic>[],
    };

void main() {
  late MockApiClient api;
  late RubricRepositoryImpl repo;

  setUpAll(registerTestFallbacks);

  setUp(() {
    api = MockApiClient();
    repo = RubricRepositoryImpl(api: api);
  });

  // ── listRubrics ───────────────────────────────────────────────────────────

  group('listRubrics', () {
    test('returns list of Rubric from API', () async {
      when(() => api.list('/rubrics')).thenAnswer(
        (_) async => listResponse([_rubricJson()]),
      );

      final result = await repo.listRubrics();

      expect(result, hasLength(1));
      expect(result.first, isA<Rubric>());
      expect(result.first.title, 'Grille orale');
      expect(result.first.criteria, hasLength(1));
    });

    test('returns empty list when none', () async {
      when(() => api.list('/rubrics')).thenAnswer(
        (_) async => listResponse([]),
      );

      final result = await repo.listRubrics();
      expect(result, isEmpty);
    });
  });

  // ── getRubric ─────────────────────────────────────────────────────────────

  group('getRubric', () {
    test('fetches rubric by id', () async {
      when(() => api.get('/rubrics/rub-1')).thenAnswer(
        (_) async => response(_rubricJson()),
      );

      final result = await repo.getRubric('rub-1');

      expect(result.id, 'rub-1');
      expect(result.maxScore, 20.0);
    });

    test('throws on API error', () async {
      when(() => api.get(any())).thenThrow(offlineError());

      expect(() => repo.getRubric('rub-1'), throwsA(isA<ApiClientError>()));
    });
  });

  // ── createRubric ──────────────────────────────────────────────────────────

  group('createRubric', () {
    test('posts rubric and returns created entity', () async {
      when(() => api.post('/rubrics', body: any(named: 'body')))
          .thenAnswer((_) async => response(_rubricJson()));

      const criterion = RubricCriterion(
        id: '',
        name: 'Prononciation',
        weight: 0.4,
        levels: [
          RubricLevel(
            id: '',
            label: 'Excellent',
            score: 8.0,
            description: '',
          ),
        ],
      );

      final result = await repo.createRubric(
        title: 'Grille orale',
        description: 'Description',
        subject: 'Français',
        criteria: [criterion],
      );

      expect(result.title, 'Grille orale');

      final body = verify(
        () => api.post('/rubrics', body: captureAny(named: 'body')),
      ).captured.first as Map<String, dynamic>;
      expect(body['title'], 'Grille orale');
      expect(body['subject'], 'Français');
      expect((body['criteria'] as List).first['name'], 'Prononciation');
    });

    test('omits null description and subject', () async {
      when(() => api.post('/rubrics', body: any(named: 'body')))
          .thenAnswer((_) async => response(_rubricJson()));

      await repo.createRubric(
        title: 'Grille',
        criteria: const [],
      );

      final body = verify(
        () => api.post('/rubrics', body: captureAny(named: 'body')),
      ).captured.first as Map<String, dynamic>;
      expect(body['description'], isNull);
      expect(body['subject'], isNull);
    });
  });

  // ── updateRubric ──────────────────────────────────────────────────────────

  group('updateRubric', () {
    test('puts updated rubric and returns entity', () async {
      when(() => api.put('/rubrics/rub-1', body: any(named: 'body')))
          .thenAnswer(
        (_) async => response(_rubricJson(title: 'Grille modifiée')),
      );

      final result = await repo.updateRubric(
        id: 'rub-1',
        title: 'Grille modifiée',
        criteria: const [],
      );

      expect(result.title, 'Grille modifiée');
    });
  });

  // ── duplicateRubric ───────────────────────────────────────────────────────

  group('duplicateRubric', () {
    test('posts duplicate and returns new rubric', () async {
      when(() => api.post('/rubrics/rub-1/duplicate', body: any(named: 'body')))
          .thenAnswer((_) async => response(_rubricJson(id: 'rub-copy')));

      final result = await repo.duplicateRubric('rub-1');

      expect(result.id, 'rub-copy');
    });
  });

  // ── gradeRubric ───────────────────────────────────────────────────────────

  group('gradeRubric', () {
    test('posts grades and returns computed result', () async {
      when(
        () => api.post(any(), body: any(named: 'body')),
      ).thenAnswer((_) async => response({}));

      const entry = RubricGradeEntry(
        criterionId: 'crit-1',
        levelId: 'lvl-1',
        score: 8.0,
        studentId: 'stu-1',
      );

      final result = await repo.gradeRubric(
        rubricId: 'rub-1',
        assignmentId: 'assign-1',
        entries: const [entry],
      );

      expect(result, isA<RubricGradeResult>());
      expect(result.totalScore, 8.0);
      expect(result.percentage, 100);
    });

    test('uses rubricId as path fallback when assignmentId is null', () async {
      when(
        () => api.post(
          '/submissions/rub-1/grade-rubric',
          body: any(named: 'body'),
        ),
      ).thenAnswer((_) async => response({}));

      await repo.gradeRubric(rubricId: 'rub-1', entries: const []);

      verify(
        () => api.post(
          '/submissions/rub-1/grade-rubric',
          body: any(named: 'body'),
        ),
      ).called(1);
    });
  });

  // ── getRubricResults ──────────────────────────────────────────────────────

  group('getRubricResults', () {
    test('fetches and returns rubric results', () async {
      when(() => api.get('/submissions/rub-1/rubric-results')).thenAnswer(
        (_) async => response(_rubricResultsJson()),
      );

      final result = await repo.getRubricResults('rub-1');

      expect(result, isA<RubricResultsResponse>());
    });
  });
}
