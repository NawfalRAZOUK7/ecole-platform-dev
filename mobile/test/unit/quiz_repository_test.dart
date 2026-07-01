import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/data/repositories_impl/lms/quiz_repository_impl.dart';
import 'package:ecole_platform/domain/entities/lms/quiz.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

Map<String, dynamic> _quizJson({String id = 'q1'}) => {
      'id': id,
      'title': 'Quiz Maths',
      'description': null,
      'subject': 'math',
      'difficulty': 'medium',
      'time_limit_minutes': 30,
      'max_attempts': 2,
      'question_count': 5,
      'total_points': 20,
      'shuffle_questions': false,
      'status': 'published',
    };

Map<String, dynamic> _questionJson({String id = 'qn1'}) => {
      'id': id,
      'question_type': 'multiple_choice',
      'question_text': 'Combien font 2+2?',
      'question_media_path': null,
      'options': {
        'choices': ['3', '4', '5'],
      },
      'points': 4,
      'order': 1,
    };

Map<String, dynamic> _attemptJson({
  String id = 'att-1',
  String status = 'in_progress',
}) =>
    {
      'id': id,
      'quiz_id': 'q1',
      'student_id': 'stu-1',
      'status': status,
      'score': null,
      'started_at': '2026-05-01T10:00:00Z',
      'submitted_at': null,
    };

void main() {
  late MockApiClient api;
  late MockCacheStore cache;
  late QuizRepositoryImpl repo;

  setUpAll(registerTestFallbacks);

  setUp(() {
    api = MockApiClient();
    cache = MockCacheStore();
    repo = QuizRepositoryImpl(api: api, cache: cache);
    when(() => cache.get(any())).thenAnswer((_) async => null);
    when(() => cache.put(any(), any(), any())).thenAnswer((_) async {});
  });

  group('getQuizzes', () {
    test('returns list of published quizzes', () async {
      when(() => api.list('/quizzes', params: any(named: 'params')))
          .thenAnswer((_) async => listResponse([_quizJson()]));

      final result = await repo.getQuizzes();

      expect(result, hasLength(1));
      expect(result.first, isA<Quiz>());
      expect(result.first.title, 'Quiz Maths');
    });

    test('passes status=published param', () async {
      when(() => api.list('/quizzes', params: any(named: 'params')))
          .thenAnswer((_) async => listResponse([]));

      await repo.getQuizzes();

      final params = verify(
        () => api.list('/quizzes', params: captureAny(named: 'params')),
      ).captured.first as Map<String, dynamic>;
      expect(params['status'], 'published');
    });
  });

  group('getQuiz', () {
    test('fetches quiz by id', () async {
      when(() => api.get('/quizzes/q1')).thenAnswer(
        (_) async => response({..._quizJson(), 'questions': <dynamic>[]}),
      );

      final result = await repo.getQuiz('q1');
      expect(result.id, 'q1');
    });
  });

  group('getQuizQuestions', () {
    test('returns questions embedded in quiz response', () async {
      when(() => api.get('/quizzes/q1')).thenAnswer(
        (_) async => response({
          ..._quizJson(),
          'questions': [_questionJson()],
        }),
      );

      final result = await repo.getQuizQuestions('q1');

      expect(result, hasLength(1));
      expect(result.first, isA<Question>());
      expect(result.first.questionText, 'Combien font 2+2?');
    });

    test('returns empty list when no questions in response', () async {
      when(() => api.get(any())).thenAnswer(
        (_) async => response({..._quizJson(), 'questions': null}),
      );

      final result = await repo.getQuizQuestions('q1');
      expect(result, isEmpty);
    });
  });

  group('startAttempt', () {
    test('posts start request and returns attempt', () async {
      when(() => api.post('/quizzes/q1/start'))
          .thenAnswer((_) async => response(_attemptJson()));

      final result = await repo.startAttempt('q1');
      expect(result, isA<QuizAttempt>());
      expect(result.status, 'in_progress');
    });
  });

  group('submitResponse', () {
    test('posts response for an attempt', () async {
      when(() => api.post('/attempts/att-1/respond', body: any(named: 'body')))
          .thenAnswer((_) async => response({}));

      await repo.submitResponse('att-1', questionId: 'qn1', answer: '4');

      final body = verify(
        () => api.post(
          '/attempts/att-1/respond',
          body: captureAny(named: 'body'),
        ),
      ).captured.first as Map<String, dynamic>;
      expect(body['question_id'], 'qn1');
      expect(body['answer'], '4');
    });
  });

  group('submitAttempt', () {
    test('posts submit for an attempt', () async {
      when(() => api.post('/attempts/att-1/submit'))
          .thenAnswer((_) async => response({}));

      await repo.submitAttempt('att-1');
      verify(() => api.post('/attempts/att-1/submit')).called(1);
    });
  });

  group('getAttemptResults', () {
    test('fetches and parses attempt results', () async {
      when(() => api.get('/attempts/att-1/results')).thenAnswer(
        (_) async => response({
          'attempt': {..._attemptJson(status: 'completed'), 'score': 16},
          'responses': <dynamic>[],
        }),
      );

      final result = await repo.getAttemptResults('att-1');
      expect(result, isA<AttemptResult>());
      expect(result.responses, isEmpty);
    });
  });

  group('getQuizResults', () {
    test('returns list of results on success', () async {
      when(() => api.list('/results/quizzes')).thenAnswer(
        (_) async => listResponse([
          {
            'quiz_id': 'q1',
            'quiz_title': 'Quiz Maths',
            'best_score': 18,
            'attempts_count': 1,
          },
        ]),
      );

      final result = await repo.getQuizResults();
      expect(result, hasLength(1));
    });

    test('returns empty list on API error (swallowed)', () async {
      when(() => api.list('/results/quizzes')).thenThrow(offlineError());

      final result = await repo.getQuizResults();
      expect(result, isEmpty);
    });
  });

  group('cacheQuizForOffline / getCachedQuestions', () {
    test('caches questions and retrieves them', () async {
      final captured = <List<Map<String, dynamic>>>[];
      when(() => cache.put(any(), any(), any())).thenAnswer((inv) async {
        captured.add(
          (inv.positionalArguments[1] as List).cast<Map<String, dynamic>>(),
        );
      });
      when(() => cache.get('quiz_offline:q1')).thenAnswer(
        (_) async => [_questionJson()],
      );

      final questions = [
        const Question(
          id: 'qn1',
          questionType: 'multiple_choice',
          questionText: 'Combien font 2+2?',
          questionMediaPath: null,
          options: {
            'choices': ['3', '4', '5'],
          },
          points: 4,
          order: 1,
        ),
      ];

      await repo.cacheQuizForOffline('q1', questions);
      final cached = await repo.getCachedQuestions('q1');

      expect(cached, hasLength(1));
      expect(cached!.first.questionText, 'Combien font 2+2?');
    });

    test('getCachedQuestions returns null when not cached', () async {
      when(() => cache.get('quiz_offline:q-miss'))
          .thenAnswer((_) async => null);

      final result = await repo.getCachedQuestions('q-miss');
      expect(result, isNull);
    });
  });
}
