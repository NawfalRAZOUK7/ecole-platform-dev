import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/repositories_impl/ai/rewards_repository.dart';
import 'package:ecole_platform/domain/entities/ai/rewards.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

void main() {
  late MockApiClient api;
  late RewardsRepositoryImpl repo;

  final rewardsJson = <String, dynamic>{
    'id': 'rw-1',
    'student_id': 'stu-1',
    'stars': 10,
    'xp': 250,
    'level': 3,
    'streak_days': 5,
    'longest_streak': 12,
    'badges': <String>['first_login', 'week_streak'],
    'last_activity_at': '2026-05-01T10:00:00.000Z',
    'level_progress': 0.6,
  };

  final leaderboardJson = <Map<String, dynamic>>[
    {
      'student_id': 'stu-1',
      'full_name': 'Alice',
      'xp': 500,
      'stars': 20,
      'level': 5,
      'rank': 1,
    },
    {
      'student_id': 'stu-2',
      'full_name': 'Bob',
      'xp': 400,
      'stars': 15,
      'level': 4,
      'rank': 2,
    },
  ];

  setUpAll(registerTestFallbacks);

  setUp(() {
    api = MockApiClient();
    repo = RewardsRepositoryImpl(api: api);
  });

  group('RewardsRepositoryImpl', () {
    group('getMyRewards', () {
      test('returns StudentRewards on success', () async {
        when(() => api.get('/rewards/me'))
            .thenAnswer((_) async => response(rewardsJson));

        final result = await repo.getMyRewards();

        expect(result, isA<StudentRewards>());
        expect(result.stars, 10);
        expect(result.xp, 250);
        expect(result.level, 3);
        expect(result.streakDays, 5);
        expect(result.longestStreak, 12);
        expect(result.badges, ['first_login', 'week_streak']);
        expect(result.lastActivityAt, isNotNull);
      });

      test('propagates ApiClientError on network failure', () async {
        when(() => api.get('/rewards/me'))
            .thenThrow(offlineError('Network unavailable'));

        expect(() => repo.getMyRewards(), throwsA(isA<ApiClientError>()));
      });
    });

    group('getStudentRewards', () {
      test('returns rewards for a specific student', () async {
        when(() => api.get('/rewards/student/stu-42'))
            .thenAnswer((_) async => response(rewardsJson));

        final result = await repo.getStudentRewards('stu-42');

        expect(result.studentId, 'stu-1');
        verify(() => api.get('/rewards/student/stu-42')).called(1);
      });

      test('throws on API error', () async {
        when(() => api.get(any())).thenThrow(
          const ApiClientError(
            404,
            ApiError(
              code: 'ERR-NOT-FOUND',
              message: 'Student not found',
              category: 'business',
              retryable: false,
            ),
          ),
        );

        expect(
          () => repo.getStudentRewards('nonexistent'),
          throwsA(isA<ApiClientError>()),
        );
      });
    });

    group('getLeaderboard', () {
      test('returns leaderboard entries for a class', () async {
        when(
          () => api.list(
            '/rewards/leaderboard/class-1',
            params: any(named: 'params'),
          ),
        ).thenAnswer((_) async => listResponse(leaderboardJson));

        final result = await repo.getLeaderboard('class-1');

        expect(result, hasLength(2));
        expect(result.first, isA<RewardsLeaderboardEntry>());
      });

      test('passes custom limit in params', () async {
        when(
          () => api.list(
            '/rewards/leaderboard/class-1',
            params: any(named: 'params'),
          ),
        ).thenAnswer((_) async => listResponse(leaderboardJson));

        await repo.getLeaderboard('class-1', limit: 5);

        final captured = verify(
          () => api.list(
            '/rewards/leaderboard/class-1',
            params: captureAny(named: 'params'),
          ),
        ).captured;
        expect(
          (captured.first as Map<String, dynamic>)['limit'],
          5,
        );
      });

      test('returns empty list when no entries', () async {
        when(
          () => api.list(
            any(),
            params: any(named: 'params'),
          ),
        ).thenAnswer((_) async => listResponse([]));

        final result = await repo.getLeaderboard('class-empty');
        expect(result, isEmpty);
      });
    });

    group('award', () {
      test('awards xp and stars to a student', () async {
        when(() => api.post('/rewards/award', body: any(named: 'body')))
            .thenAnswer((_) async => response(rewardsJson));

        final result = await repo.award(
          studentId: 'stu-1',
          eventType: 'quiz_completed',
          stars: 3,
          xp: 50,
          sourceType: 'quiz',
          sourceId: 'quiz-99',
        );

        expect(result.stars, 10);
        final capturedBody = verify(
          () => api.post(
            '/rewards/award',
            body: captureAny(named: 'body'),
          ),
        ).captured.first as Map<String, dynamic>;
        expect(capturedBody['student_id'], 'stu-1');
        expect(capturedBody['event_type'], 'quiz_completed');
        expect(capturedBody['stars'], 3);
        expect(capturedBody['xp'], 50);
        expect(capturedBody['source_type'], 'quiz');
        expect(capturedBody['source_id'], 'quiz-99');
      });

      test('omits optional fields when null', () async {
        when(() => api.post('/rewards/award', body: any(named: 'body')))
            .thenAnswer((_) async => response(rewardsJson));

        await repo.award(
          studentId: 'stu-1',
          eventType: 'login',
        );

        final capturedBody = verify(
          () => api.post(
            '/rewards/award',
            body: captureAny(named: 'body'),
          ),
        ).captured.first as Map<String, dynamic>;
        expect(capturedBody.containsKey('source_type'), isFalse);
        expect(capturedBody.containsKey('source_id'), isFalse);
      });

      test('throws on error', () async {
        when(() => api.post(any(), body: any(named: 'body')))
            .thenThrow(offlineError());

        expect(
          () => repo.award(studentId: 'stu-1', eventType: 'test'),
          throwsA(isA<ApiClientError>()),
        );
      });
    });
  });
}
