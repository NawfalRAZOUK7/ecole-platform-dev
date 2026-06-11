import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/repositories_impl/reports/reporting_repository_impl.dart';
import 'package:ecole_platform/domain/entities/reports/reporting.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

Map<String, dynamic> _jobJson({
  String id = 'job-1',
  String type = 'bulletin',
  String status = 'completed',
  String? downloadUrl,
}) =>
    {
      'id': id,
      'type': type,
      'status': status,
      'parameters': <String, dynamic>{},
      'created_at': '2026-05-01T10:00:00Z',
      'completed_at': status == 'completed' ? '2026-05-01T10:02:00Z' : null,
      'expires_at': null,
      'error_message': null,
      'download_url': downloadUrl,
      'cache_hit': false,
      'local_file_path': null,
    };

Map<String, dynamic> _metricJson({double current = 0}) => {
      'current': current,
      'previous': null,
      'change': null,
      'change_pct': null,
    };

void main() {
  late MockApiClient api;
  late MockReportsStore store;
  late ReportingRepositoryImpl repo;

  setUpAll(registerTestFallbacks);

  setUp(() {
    api = MockApiClient();
    store = MockReportsStore();
    repo = ReportingRepositoryImpl(api: api, reportsStore: store);

    // Default store stubs
    when(() => store.readAll()).thenAnswer((_) async => []);
    when(() => store.upsert(any(), filePath: any(named: 'filePath')))
        .thenAnswer((_) async {});
  });

  // ── getReportOptions ───────────────────────────────────────────────────────

  group('getReportOptions', () {
    test('returns parsed ReportOptions from API', () async {
      when(() => api.get('/reports/options', params: any(named: 'params')))
          .thenAnswer(
        (_) async => response({
          'classes': [
            {'code': 'CP', 'name': 'CP-A', 'id': 'cls-1'},
          ],
          'periods': [
            {'id': 'p1', 'label': 'T1'},
          ],
          'students': [
            {'full_name': 'Alice', 'email': 'alice@school.ma', 'id': 'stu-1'},
          ],
          'parents': [
            {
              'full_name': 'M. Alaoui',
              'email': 'alaoui@gmail.com',
              'id': 'par-1'
            },
          ],
        }),
      );

      final result = await repo.getReportOptions();

      expect(result, isA<ReportOptions>());
      expect(result.classes, hasLength(1));
      expect(result.periods, hasLength(1));
      expect(result.students, hasLength(1));
      expect(result.parents, hasLength(1));
    });

    test('returns empty lists when API response has no collections', () async {
      when(() => api.get('/reports/options', params: any(named: 'params')))
          .thenAnswer((_) async => response({}));

      final result = await repo.getReportOptions();

      expect(result.classes, isEmpty);
      expect(result.periods, isEmpty);
    });

    test('passes type and classId params when provided', () async {
      when(() => api.get('/reports/options', params: any(named: 'params')))
          .thenAnswer((_) async => response({}));

      await repo.getReportOptions(type: 'attendance', classId: 'cls-1');

      final captured = verify(
        () => api.get('/reports/options', params: captureAny(named: 'params')),
      ).captured.first as Map<String, dynamic>;
      expect(captured['type'], 'attendance');
      expect(captured['class_id'], 'cls-1');
    });

    test('omits empty params', () async {
      when(() => api.get('/reports/options', params: any(named: 'params')))
          .thenAnswer((_) async => response({}));

      await repo.getReportOptions(type: '', classId: '');

      final captured = verify(
        () => api.get('/reports/options', params: captureAny(named: 'params')),
      ).captured.first as Map<String, dynamic>;
      expect(captured.containsKey('type'), isFalse);
      expect(captured.containsKey('class_id'), isFalse);
    });

    test('propagates API error', () async {
      when(() => api.get(any(), params: any(named: 'params')))
          .thenThrow(offlineError());

      expect(() => repo.getReportOptions(), throwsA(isA<ApiClientError>()));
    });
  });

  // ── getReportJobs ─────────────────────────────────────────────────────────

  group('getReportJobs', () {
    test('fetches jobs from API and returns paginated list', () async {
      when(
        () => api.list('/reports', params: any(named: 'params')),
      ).thenAnswer((_) async => listResponse([_jobJson()]));

      final result = await repo.getReportJobs();

      expect(result.items, hasLength(1));
      expect(result.items.first.type, 'bulletin');
    });

    test('passes cursor, type, status params to API', () async {
      when(
        () => api.list('/reports', params: any(named: 'params')),
      ).thenAnswer((_) async => listResponse([]));

      await repo.getReportJobs(
          cursor: 'cur-1', type: 'grades', status: 'completed');

      final captured = verify(
        () => api.list('/reports', params: captureAny(named: 'params')),
      ).captured.first as Map<String, dynamic>;
      expect(captured['cursor'], 'cur-1');
      expect(captured['type'], 'grades');
      expect(captured['status'], 'completed');
    });

    test('falls back to cached reports on offline error (first page)',
        () async {
      when(
        () => api.list(any(), params: any(named: 'params')),
      ).thenThrow(offlineError());
      when(() => store.readAll()).thenAnswer((_) async => [_jobJson()]);

      final result = await repo.getReportJobs();

      expect(result.items, hasLength(1));
      expect(result.hasMore, isFalse);
    });

    test('rethrows offline error when fetching paginated pages (cursor set)',
        () async {
      when(
        () => api.list(any(), params: any(named: 'params')),
      ).thenThrow(offlineError());

      expect(
        () => repo.getReportJobs(cursor: 'page-2'),
        throwsA(isA<ApiClientError>()),
      );
    });
  });

  // ── generateReport ────────────────────────────────────────────────────────

  group('generateReport', () {
    test('posts report request and returns ReportJob', () async {
      when(() => api.post('/reports/generate', body: any(named: 'body')))
          .thenAnswer((_) async => response(_jobJson(status: 'pending')));

      final result = await repo.generateReport(
        type: 'grades',
        locale: 'fr',
        classId: 'cls-1',
        periodId: 'p1',
      );

      expect(result, isA<ReportJob>());
      expect(result.type, 'bulletin');
    });

    test('includes all optional params in body', () async {
      when(() => api.post('/reports/generate', body: any(named: 'body')))
          .thenAnswer((_) async => response(_jobJson()));

      await repo.generateReport(
        type: 'attendance',
        locale: 'ar',
        periodId: 'p1',
        classId: 'cls-1',
        studentId: 'stu-1',
        parentId: 'par-1',
        fromDate: '2026-01-01',
        toDate: '2026-06-01',
        compare: true,
      );

      final body = verify(
        () => api.post('/reports/generate', body: captureAny(named: 'body')),
      ).captured.first as Map<String, dynamic>;
      expect(body['type'], 'attendance');
      expect(body['locale'], 'ar');
      expect(body['compare'], isTrue);
      expect(body['period_id'], 'p1');
      expect(body['class_id'], 'cls-1');
      expect(body['student_id'], 'stu-1');
      expect(body['parent_id'], 'par-1');
      expect(body['from_date'], '2026-01-01');
      expect(body['to_date'], '2026-06-01');
    });

    test('omits empty optional params', () async {
      when(() => api.post('/reports/generate', body: any(named: 'body')))
          .thenAnswer((_) async => response(_jobJson()));

      await repo.generateReport(type: 'bulletin', locale: 'fr');

      final body = verify(
        () => api.post('/reports/generate', body: captureAny(named: 'body')),
      ).captured.first as Map<String, dynamic>;
      expect(body.containsKey('period_id'), isFalse);
      expect(body.containsKey('class_id'), isFalse);
    });

    test('throws on API failure', () async {
      when(() => api.post(any(), body: any(named: 'body')))
          .thenThrow(offlineError());

      expect(
        () => repo.generateReport(type: 'grades', locale: 'fr'),
        throwsA(isA<ApiClientError>()),
      );
    });
  });

  // ── getCachedReports ──────────────────────────────────────────────────────

  group('getCachedReports', () {
    test('reads all reports from store', () async {
      when(() => store.readAll()).thenAnswer((_) async => [_jobJson()]);

      final result = await repo.getCachedReports();

      expect(result, hasLength(1));
      verify(() => store.readAll()).called(1);
    });

    test('returns empty list when store is empty', () async {
      when(() => store.readAll()).thenAnswer((_) async => []);

      final result = await repo.getCachedReports();

      expect(result, isEmpty);
    });
  });

  // ── Analytics getters ─────────────────────────────────────────────────────

  group('getOverview', () {
    test('parses analytics overview from API', () async {
      when(() => api.get('/analytics/overview', params: any(named: 'params')))
          .thenAnswer(
        (_) async => response({'metrics': <dynamic>[]}),
      );

      final result = await repo.getOverview(
        fromDate: '2026-01-01',
        toDate: '2026-06-01',
        compare: false,
      );

      expect(result, isA<AnalyticsOverview>());
      expect(result.metrics, isEmpty);
    });

    test('passes correct params', () async {
      when(() => api.get('/analytics/overview', params: any(named: 'params')))
          .thenAnswer((_) async => response({'metrics': <dynamic>[]}));

      await repo.getOverview(
          fromDate: '2026-01-01', toDate: '2026-06-01', compare: true);

      final params = verify(
        () =>
            api.get('/analytics/overview', params: captureAny(named: 'params')),
      ).captured.first as Map<String, dynamic>;
      expect(params['from'], '2026-01-01');
      expect(params['compare'], 'true');
    });
  });

  group('getAttendance', () {
    test('parses attendance analytics from API', () async {
      when(() => api.get('/analytics/attendance', params: any(named: 'params')))
          .thenAnswer(
        (_) async => response({
          'summary': {'rate': _metricJson(current: 92.5), 'total_records': 240},
          'series': <dynamic>[],
        }),
      );

      final result = await repo.getAttendance(
        fromDate: '2026-01-01',
        toDate: '2026-06-01',
        compare: false,
        period: 'week',
      );

      expect(result, isA<AttendanceAnalytics>());
      expect(result.totalRecords, 240);
    });
  });

  group('getGrades', () {
    test('parses grades analytics from API', () async {
      when(() => api.get('/analytics/grades', params: any(named: 'params')))
          .thenAnswer(
        (_) async => response({
          'summary': {'average': _metricJson(current: 14.5), 'count': 120},
          'distribution': <dynamic>[],
        }),
      );

      final result = await repo.getGrades(
        fromDate: '2026-01-01',
        toDate: '2026-06-01',
        compare: false,
      );

      expect(result, isA<GradesAnalytics>());
      expect(result.count, 120);
    });

    test('passes optional subject param', () async {
      when(() => api.get('/analytics/grades', params: any(named: 'params')))
          .thenAnswer(
        (_) async => response({
          'summary': <String, dynamic>{},
          'distribution': <dynamic>[],
        }),
      );

      await repo.getGrades(
        fromDate: '2026-01-01',
        toDate: '2026-06-01',
        compare: false,
        subject: 'math',
      );

      final params = verify(
        () => api.get('/analytics/grades', params: captureAny(named: 'params')),
      ).captured.first as Map<String, dynamic>;
      expect(params['subject'], 'math');
    });
  });

  group('getBilling', () {
    test('parses billing analytics from API', () async {
      when(() => api.get('/analytics/billing', params: any(named: 'params')))
          .thenAnswer(
        (_) async => response({
          'summary': {
            'invoiced': 50000.0,
            'paid': 42000.0,
            'outstanding': 8000.0,
            'collection_rate': _metricJson(current: 84.0),
          },
          'series': <dynamic>[],
        }),
      );

      final result = await repo.getBilling(
        fromDate: '2026-01-01',
        toDate: '2026-06-01',
        compare: false,
        period: 'month',
      );

      expect(result, isA<BillingAnalytics>());
      expect(result.paid, 42000.0);
    });
  });

  group('getEngagement', () {
    test('parses engagement analytics from API', () async {
      when(() => api.get('/analytics/engagement', params: any(named: 'params')))
          .thenAnswer(
        (_) async => response({
          'active_users': _metricJson(current: 185),
          'content_views': _metricJson(current: 420),
          'quiz_completions': _metricJson(current: 95),
          'avg_session_minutes': _metricJson(current: 22),
        }),
      );

      final result = await repo.getEngagement(
        fromDate: '2026-01-01',
        toDate: '2026-06-01',
        compare: false,
      );

      expect(result, isA<EngagementAnalytics>());
    });
  });

  // ── Schedules ─────────────────────────────────────────────────────────────

  group('createSchedule', () {
    final scheduleJson = {
      'id': 'sch-1',
      'name': 'Weekly bulletin',
      'report_type': 'bulletin',
      'cron_expression': '0 8 * * MON',
      'parameters': <String, dynamic>{},
      'is_active': true,
      'created_at': '2026-05-01T00:00:00Z',
      'last_run_at': null,
      'next_run_at': null,
    };

    test('creates schedule and returns it', () async {
      when(() => api.post('/reports/schedules', body: any(named: 'body')))
          .thenAnswer((_) async => response(scheduleJson));

      final result = await repo.createSchedule(
        name: 'Weekly bulletin',
        reportType: 'bulletin',
        cronExpression: '0 8 * * MON',
      );

      expect(result, isA<ReportSchedule>());
      expect(result.name, 'Weekly bulletin');
    });

    test('listSchedules returns all schedules', () async {
      when(() => api.list('/reports/schedules'))
          .thenAnswer((_) async => listResponse([scheduleJson]));

      final result = await repo.listSchedules();

      expect(result, hasLength(1));
      expect(result.first.reportType, 'bulletin');
    });

    test('updateSchedule updates and returns schedule', () async {
      when(() => api.put('/reports/schedules/sch-1', body: any(named: 'body')))
          .thenAnswer(
              (_) async => response({...scheduleJson, 'is_active': false}));

      final result = await repo.updateSchedule(id: 'sch-1', isActive: false);

      expect(result.isActive, isFalse);
    });

    test('deleteSchedule calls delete endpoint', () async {
      when(() => api.delete('/reports/schedules/sch-1'))
          .thenAnswer((_) async => response({}));

      await repo.deleteSchedule('sch-1');

      verify(() => api.delete('/reports/schedules/sch-1')).called(1);
    });

    test('runSchedule triggers run and returns job', () async {
      when(
        () =>
            api.post('/reports/schedules/sch-1/run', body: any(named: 'body')),
      ).thenAnswer((_) async => response(_jobJson(status: 'pending')));

      final result = await repo.runSchedule('sch-1');

      expect(result, isA<ReportJob>());
    });
  });
}
