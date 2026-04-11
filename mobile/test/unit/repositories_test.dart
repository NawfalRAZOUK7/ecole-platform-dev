import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/repositories_impl/admin_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/attendance_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/auth_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/budget_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/calendar_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/compliance_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content_library_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/content_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/document_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/feed_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/financial_health_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/gradebook_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/invoice_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/micro_school_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/notification_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/question_bank_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/quiz_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/reporting_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/result_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/rubric_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/skills_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/sync_repository_impl.dart';
import 'package:ecole_platform/data/repositories_impl/teacher_repository_impl.dart';
import 'package:ecole_platform/domain/entities/rubric.dart';

import '../helpers/test_mocks.dart';
import '../helpers/test_services.dart';

ApiResponse<Map<String, dynamic>> _response(Map<String, dynamic> data) {
  return ApiResponse<Map<String, dynamic>>(data: data);
}

ApiListResponse<Map<String, dynamic>> _listResponse(
  List<Map<String, dynamic>> data, {
  String? nextCursor,
  bool hasMore = false,
}) {
  return ApiListResponse<Map<String, dynamic>>(
    data: data,
    nextCursor: nextCursor,
    hasMore: hasMore,
  );
}

ApiClientError _offlineError() {
  return const ApiClientError(
    503,
    ApiError(
      code: 'ERR-OFFLINE',
      message: 'Offline',
      category: 'network',
      retryable: true,
    ),
  );
}

void main() {
  group('Repository implementations', () {
    setUpAll(registerTestFallbacks);

    test('AdminRepositoryImpl maps dashboard responses', () async {
      final api = MockApiClient();
      final repository = AdminRepositoryImpl(api: api);

      when(() => api.get('/admin/dashboard')).thenAnswer(
        (_) async => _response(
          {
            'total_users': 120,
            'active_sessions': 18,
            'active_invitations': 4,
            'audit_events_24h': 26,
            'pending_justifications': 3,
            'users_by_role': {'PAR': 60, 'STD': 40},
          },
        ),
      );

      final dashboard = await repository.getDashboard();

      expect(dashboard.totalUsers, 120);
      expect(dashboard.usersByRole['PAR'], 60);
    });

    test('AttendanceRepositoryImpl loads class attendance and writes cache',
        () async {
      final api = MockApiClient();
      final store = MockAttendanceStore();
      final repository = AttendanceRepositoryImpl(api: api, store: store);

      when(
        () => store.readClassAttendance('class-1', '2026-04-11'),
      ).thenAnswer((_) async => null);
      when(
        () => api.list(
          '/attendance/class/class-1',
          params: {'date': '2026-04-11'},
        ),
      ).thenAnswer(
        (_) async => _listResponse(
          const [
            {
              'id': 'attendance-1',
              'student_id': 'student-1',
              'date': '2026-04-11',
              'status': 'present',
            },
          ],
        ),
      );
      when(
        () => store.writeClassAttendance(
          'class-1',
          '2026-04-11',
          const [
            {
              'id': 'attendance-1',
              'student_id': 'student-1',
              'date': '2026-04-11',
              'status': 'present',
            },
          ],
        ),
      ).thenAnswer((_) async {});

      final entries = await repository.getClassAttendance(
        'class-1',
        date: '2026-04-11',
      );

      expect(entries.single.id, 'attendance-1');
      verify(
        () => store.writeClassAttendance(
          'class-1',
          '2026-04-11',
          const [
            {
              'id': 'attendance-1',
              'student_id': 'student-1',
              'date': '2026-04-11',
              'status': 'present',
            },
          ],
        ),
      ).called(1);
    });

    test('AuthRepositoryImpl login stores access and refresh tokens', () async {
      final api = MockApiClient();
      final tokenStorage = TestSecureTokenStorage();
      final repository = AuthRepositoryImpl(
        api: api,
        tokenStorage: tokenStorage,
      );

      when(
        () => api.post(
          '/auth/login',
          body: any(named: 'body'),
          skipAuth: true,
        ),
      ).thenAnswer(
        (_) async => _response(
          {
            'access_token': 'access-1',
            'refresh_token': 'refresh-1',
          },
        ),
      );
      when(() => api.setAccessToken(any())).thenReturn(null);

      final result = await repository.login(
        'parent@ecole.test',
        'secret',
        'school-1',
        deviceName: 'iPhone',
      );

      expect(result.accessToken, 'access-1');
      expect(await tokenStorage.getRefreshToken(), 'refresh-1');
      verify(() => api.setAccessToken('access-1')).called(1);
    });

    test('AuthRepositoryImpl returns 2FA challenges without storing tokens',
        () async {
      final api = MockApiClient();
      final tokenStorage = TestSecureTokenStorage();
      final repository = AuthRepositoryImpl(
        api: api,
        tokenStorage: tokenStorage,
      );

      when(
        () => api.post(
          '/auth/login',
          body: any(named: 'body'),
          skipAuth: true,
        ),
      ).thenAnswer(
        (_) async => _response(
          {
            'requires_2fa': true,
            'temp_token': 'temp-1',
          },
        ),
      );

      final result = await repository.login(
        'parent@ecole.test',
        'secret',
        'school-1',
      );

      expect(result.requires2fa, isTrue);
      expect(result.tempToken, 'temp-1');
      expect(await tokenStorage.getRefreshToken(), isNull);
      verifyNever(() => api.setAccessToken(any()));
    });

    test('BudgetRepositoryImpl aggregates requests across allocations',
        () async {
      final api = MockApiClient();
      final repository = BudgetRepositoryImpl(api: api);

      when(() => api.get('/budgets/budget-1')).thenAnswer(
        (_) async => _response(
          {
            'id': 'budget-1',
            'name': 'STEM',
            'code': 'B-1',
            'status': 'active',
            'total_amount': 1000,
            'allocated_amount': 600,
            'spent_amount': 300,
            'currency': 'MAD',
          },
        ),
      );
      when(() => api.list('/budgets/budget-1/allocations')).thenAnswer(
        (_) async => _listResponse(
          const [
            {
              'id': 'allocation-1',
              'budget_id': 'budget-1',
              'label': 'Supplies',
              'amount': 500,
              'committed_amount': 100,
              'spent_amount': 50,
              'currency': 'MAD',
            },
          ],
        ),
      );
      when(
        () => api.list(
          '/budgets/allocations/allocation-1/requests',
          params: {'status': 'pending'},
        ),
      ).thenAnswer(
        (_) async => _listResponse(
          const [
            {
              'id': 'request-1',
              'allocation_id': 'allocation-1',
              'status': 'pending',
              'amount': 120,
              'currency': 'MAD',
              'description': 'Lab kits',
            },
          ],
        ),
      );

      final requests = await repository.listBudgetRequests(
        params: {'budget_id': 'budget-1', 'status': 'pending'},
      );

      expect(requests, hasLength(1));
      expect(requests.single.budgetId, 'budget-1');
      expect(requests.single.description, 'Lab kits');
    });

    test('CalendarRepositoryImpl falls back to cached events when offline',
        () async {
      final api = MockApiClient();
      final eventsStore = MockEventsStore();
      final repository = CalendarRepositoryImpl(
        api: api,
        eventsStore: eventsStore,
      );

      when(
        () => api.list(
          '/events',
          params: {
            'from': '2026-04-01',
            'to': '2026-04-30',
          },
        ),
      ).thenThrow(_offlineError());
      when(() => eventsStore.readMonth('2026-04')).thenAnswer(
        (_) async => const [
          {
            'id': 'event-1',
            'title_fr': 'Réunion',
            'start_at': '2026-04-02T10:00:00Z',
            'end_at': '2026-04-02T11:00:00Z',
          },
        ],
      );

      final events = await repository.getEvents(
        fromDate: '2026-04-01',
        toDate: '2026-04-30',
      );

      expect(events.single.id, 'event-1');
      expect(events.single.titleFr, 'Réunion');
    });

    test('ComplianceRepositoryImpl maps dashboard responses', () async {
      final api = MockApiClient();
      final repository = ComplianceRepositoryImpl(api: api);

      when(
        () => api.get(
          '/compliance/dashboard',
          params: {'academic_year_id': 'year-1'},
        ),
      ).thenAnswer(
        (_) async => _response(
          {
            'coverage_rate': 91.5,
            'objectives_covered_rate': 88.2,
            'missing_coverage_rate': 11.8,
            'metrics': [
              {'label': 'Arabic', 'value': 95.0},
            ],
          },
        ),
      );

      final dashboard = await repository.getDashboard(academicYearId: 'year-1');

      expect(dashboard.coverageRate, 91.5);
      expect(dashboard.metrics.single.label, 'Arabic');
    });

    test('ContentLibraryRepositoryImpl caches class content on API success',
        () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = ContentLibraryRepositoryImpl(api: api, cache: cache);

      when(() => cache.get('class_content:class-1'))
          .thenAnswer((_) async => null);
      when(() => api.list('/classes/class-1/content')).thenAnswer(
        (_) async => _listResponse(
          const [
            {
              'id': 'assigned-1',
              'content_item_id': 'content-1',
              'title': 'Reading assignment',
              'content_type': 'document',
              'progress': 'started',
            },
          ],
        ),
      );
      when(
        () => cache.put(
          'class_content:class-1',
          any(),
          any(),
        ),
      ).thenAnswer((_) async {});

      final items = await repository.getClassContent('class-1');

      expect(items.single.contentItemId, 'content-1');
      verify(
        () => cache.put(
          'class_content:class-1',
          const [
            {
              'id': 'assigned-1',
              'content_item_id': 'content-1',
              'title': 'Reading assignment',
              'content_type': 'document',
              'progress': 'started',
            },
          ],
          any(),
        ),
      ).called(1);
    });

    test('ContentRepositoryImpl returns cached pages without hitting the API',
        () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = ContentRepositoryImpl(api: api, cache: cache);

      when(() => cache.get('content:first::')).thenAnswer(
        (_) async => const [
          {
            'id': 'content-1',
            'school_id': 'school-1',
            'title': 'Math worksheet',
            'content_type': 'worksheet',
            'status': 'published',
          },
        ],
      );

      final page = await repository.getContentItems();

      expect(page.items.single.id, 'content-1');
      expect(page.hasMore, isFalse);
      verifyNever(() => api.list(any(), params: any(named: 'params')));
    });

    test('DocumentRepositoryImpl falls back to default categories offline',
        () async {
      final api = MockApiClient();
      final store = MockDocumentsStore();
      final repository =
          DocumentRepositoryImpl(api: api, documentsStore: store);

      when(() => api.get('/documents/options')).thenThrow(_offlineError());

      final options = await repository.getDocumentOptions();

      expect(options.categories, containsAll(['certificate', 'report_card']));
      expect(options.students, isEmpty);
    });

    test('FeedRepositoryImpl fetches and caches feed pages', () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = FeedRepositoryImpl(api: api, cache: cache);

      when(() => cache.get('feed:first')).thenAnswer((_) async => null);
      when(() => api.list('/feed', params: {})).thenAnswer(
        (_) async => _listResponse(
          const [
            {
              'id': 'feed-1',
              'school_id': 'school-1',
              'parent_id': 'parent-1',
              'source_type': 'announcement',
              'title': 'School closes early',
              'created_at': '2026-04-10T08:00:00Z',
            },
          ],
          nextCursor: 'cursor-2',
          hasMore: true,
        ),
      );
      when(() => cache.put('feed:first', any(), any()))
          .thenAnswer((_) async {});

      final page = await repository.getFeed();

      expect(page.items.single.title, 'School closes early');
      expect(page.nextCursor, 'cursor-2');
      expect(page.hasMore, isTrue);
    });

    test('FinancialHealthRepositoryImpl maps dashboard snapshots', () async {
      final api = MockApiClient();
      final repository = FinancialHealthRepositoryImpl(api: api);

      when(() => api.get('/financial-health/dashboard')).thenAnswer(
        (_) async => _response(
          {
            'retention_rate': 93.0,
            'net_cashflow': 12000.0,
            'cost_per_student': 850.0,
            'snapshot': {
              'snapshot_date': '2026-04-01',
              'revenue': 20000.0,
              'expenses': 8000.0,
              'net_position': 12000.0,
            },
          },
        ),
      );

      final dashboard = await repository.getDashboard();

      expect(dashboard.retentionRate, 93.0);
      expect(dashboard.snapshot.snapshotDate, '2026-04-01');
    });

    test('GradebookRepositoryImpl loads class grids and caches them', () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = GradebookRepositoryImpl(api: api, cache: cache);

      when(() => cache.get('gradebook:grid:class-1'))
          .thenAnswer((_) async => null);
      when(() => api.get('/gradebook/classes/class-1')).thenAnswer(
        (_) async => _response(
          {
            'class_id': 'class-1',
            'class_name': '6A',
            'columns': [
              {
                'assessment_id': 'assessment-1',
                'title': 'Quiz 1',
                'weight': 0.4,
                'date': '2026-04-10',
                'type': 'quiz',
              },
            ],
            'entries': [
              {
                'student_id': 'student-1',
                'student_name': 'Student Example',
                'grades': {'assessment-1': 17},
                'weighted_average': 17.0,
              },
            ],
          },
        ),
      );
      when(() => cache.put('gradebook:grid:class-1', any(), any()))
          .thenAnswer((_) async {});

      final grid = await repository.getClassGradebook('class-1');

      expect(grid.className, '6A');
      expect(grid.entries.single.grades['assessment-1'], 17.0);
    });

    test('InvoiceRepositoryImpl invalidates caches after payments', () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = InvoiceRepositoryImpl(api: api, cache: cache);

      when(
        () => api.post(
          '/payments/initiate',
          body: any(named: 'body'),
        ),
      ).thenAnswer(
        (_) async => _response(
          {
            'id': 'payment-1',
            'invoice_id': 'invoice-1',
            'amount': 500.0,
            'method': 'cash',
            'status': 'initiated',
            'created_at': '2026-04-10T09:00:00Z',
          },
        ),
      );
      when(() => cache.invalidatePrefix('invoices:')).thenAnswer((_) async {});

      final payment = await repository.createPayment(
        invoiceId: 'invoice-1',
        amount: 500,
        method: 'cash',
      );

      expect(payment.id, 'payment-1');
      verify(() => cache.invalidatePrefix('invoices:')).called(1);
    });

    test('MicroSchoolRepositoryImpl derives progress from log responses',
        () async {
      final api = MockApiClient();
      final repository = MicroSchoolRepositoryImpl(api: api);

      when(
        () => api.list(
          '/micro/progress-logs',
          params: {'micro_school_id': 'micro-1'},
        ),
      ).thenAnswer(
        (_) async => _listResponse(
          const [
            {'student_id': 'student-1', 'date': '2026-04-01'},
            {'student_id': 'student-2', 'date': '2026-04-02'},
          ],
        ),
      );

      final progress = await repository.getProgress('micro-1');

      expect(progress.activeStudents, 2);
      expect(progress.averageProgress, 100);
      expect(progress.series, hasLength(2));
    });

    test('NotificationRepositoryImpl uses offline store fallback', () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final notificationsStore = MockNotificationsStore();
      final repository = NotificationRepositoryImpl(
        api: api,
        cache: cache,
        notificationsStore: notificationsStore,
      );

      when(
        () => cache.get('notifications:first:all:all'),
      ).thenAnswer((_) async => null);
      when(
        () => api.list('/notifications', params: any(named: 'params')),
      ).thenThrow(_offlineError());
      when(() => notificationsStore.readAll()).thenAnswer(
        (_) async => const [
          {
            'id': 'notification-1',
            'school_id': 'school-1',
            'user_id': 'user-1',
            'title': 'Offline notification',
            'category': 'system',
            'created_at': '2026-04-10T08:00:00Z',
          },
        ],
      );

      final page = await repository.getNotifications();

      expect(page.items.single.title, 'Offline notification');
      expect(page.hasMore, isFalse);
    });

    test('QuestionBankRepositoryImpl maps aggregate stats', () async {
      final api = MockApiClient();
      final repository = QuestionBankRepositoryImpl(api: api);

      when(() => api.get('/question-bank/stats')).thenAnswer(
        (_) async => _response(
          {
            'total': 40,
            'by_subject': {'math': 20},
            'by_type': {'mcq': 30},
            'by_difficulty': {'easy': 10},
          },
        ),
      );

      final stats = await repository.getStats();

      expect(stats.total, 40);
      expect(stats.bySubject['math'], 20);
    });

    test('QuizRepositoryImpl maps attempt results with responses', () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = QuizRepositoryImpl(api: api, cache: cache);

      when(() => api.get('/attempts/attempt-1/results')).thenAnswer(
        (_) async => _response(
          {
            'attempt': {
              'id': 'attempt-1',
              'quiz_id': 'quiz-1',
              'attempt_no': 1,
              'status': 'completed',
              'score': 9,
              'max_score': 10,
            },
            'responses': [
              {
                'question_id': 'question-1',
                'question_type': 'MCQ',
                'question_text': 'What is 2 + 2?',
                'student_answer': 'B',
                'correct_answer': 'B',
                'is_correct': true,
                'points_earned': 5,
                'points': 5,
              },
            ],
          },
        ),
      );

      final result = await repository.getAttemptResults('attempt-1');

      expect(result.attempt.id, 'attempt-1');
      expect(result.responses.single.isCorrect, isTrue);
    });

    test('ReportingRepositoryImpl merges local file paths into report jobs',
        () async {
      final api = MockApiClient();
      final reportsStore = MockReportsStore();
      final repository = ReportingRepositoryImpl(
        api: api,
        reportsStore: reportsStore,
      );

      when(
        () => api.list('/reports', params: {'limit': 10}),
      ).thenAnswer(
        (_) async => _listResponse(
          const [
            {
              'id': 'report-1',
              'type': 'student_report_card',
              'status': 'ready',
              'parameters': <String, dynamic>{},
              'created_at': '2026-04-10T08:00:00Z',
              'download_url': 'https://files.ecole.test/report-1.pdf',
            },
          ],
        ),
      );
      when(() => reportsStore.readAll()).thenAnswer(
        (_) async => const [
          {
            'id': 'report-1',
            'local_file_path': '/tmp/report-1.pdf',
          },
        ],
      );

      final page = await repository.getReportJobs();

      expect(page.items.single.localFilePath, '/tmp/report-1.pdf');
    });

    test('ResultRepositoryImpl fetches results and caches them', () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = ResultRepositoryImpl(api: api, cache: cache);

      when(() => cache.get('results:first')).thenAnswer((_) async => null);
      when(() => api.list('/results', params: {})).thenAnswer(
        (_) async => _listResponse(
          const [
            {
              'assignment_id': 'assignment-1',
              'assignment_title': 'Essay',
              'course_title': 'French',
              'submission_id': 'submission-1',
              'status': 'graded',
              'score': 16,
              'total_points': 20,
            },
          ],
        ),
      );
      when(() => cache.put('results:first', any(), any()))
          .thenAnswer((_) async {});

      final page = await repository.getResults();

      expect(page.items.single.assignmentId, 'assignment-1');
      verify(() => cache.put('results:first', any(), any())).called(1);
    });

    test('RubricRepositoryImpl posts grades and returns computed totals',
        () async {
      final api = MockApiClient();
      final repository = RubricRepositoryImpl(api: api);
      final entries = const [
        RubricGradeEntry(
          studentId: 'student-1',
          criterionId: 'criterion-1',
          levelId: 'level-1',
          score: 4,
        ),
        RubricGradeEntry(
          studentId: 'student-1',
          criterionId: 'criterion-2',
          levelId: 'level-2',
          score: 5,
        ),
      ];

      when(
        () => api.post(
          '/submissions/assignment-1/grade-rubric',
          body: any(named: 'body'),
        ),
      ).thenAnswer((_) async => _response(const {}));

      final result = await repository.gradeRubric(
        rubricId: 'rubric-1',
        assignmentId: 'assignment-1',
        entries: entries,
      );

      expect(result.rubricId, 'rubric-1');
      expect(result.totalScore, 9);
      expect(result.entries, hasLength(2));
    });

    test('SkillsRepositoryImpl maps student passports', () async {
      final api = MockApiClient();
      final repository = SkillsRepositoryImpl(api: api);

      when(
        () => api.get(
          '/skills/passport/student-1',
          params: {'academic_year_id': 'year-1'},
        ),
      ).thenAnswer(
        (_) async => _response(
          {
            'student_id': 'student-1',
            'student_name': 'Student Example',
            'academic_year_id': 'year-1',
            'overall_score': 88.0,
            'dimensions': [
              {
                'id': 'skill-1',
                'label': 'Creativity',
                'score': 91.0,
              },
            ],
          },
        ),
      );

      final passport = await repository.getPassport(
        'student-1',
        academicYearId: 'year-1',
      );

      expect(passport.studentName, 'Student Example');
      expect(passport.dimensions.single.label, 'Creativity');
    });

    test('SyncRepositoryImpl maps status payloads', () async {
      final api = MockApiClient();
      final repository = SyncRepositoryImpl(api: api);

      when(
        () => api.get(
          '/sync/status',
          params: {'device_id': 'device-1'},
        ),
      ).thenAnswer(
        (_) async => _response(
          {
            'pending_operations': 3,
            'last_sync_at': '2026-04-10T09:00:00Z',
            'last_checkpoint': 'cp-1',
            'online': true,
          },
        ),
      );

      final status = await repository.getStatus('device-1');

      expect(status.pendingOperations, 3);
      expect(status.lastCheckpoint, 'cp-1');
    });

    test('TeacherRepositoryImpl maps paginated assignments', () async {
      final api = MockApiClient();
      final repository = TeacherRepositoryImpl(api: api);

      when(
        () => api.list('/assignments', params: {'course_id': 'course-1'}),
      ).thenAnswer(
        (_) async => _listResponse(
          const [
            {
              'id': 'assignment-1',
              'course_id': 'course-1',
              'title': 'Homework 1',
              'description': 'Complete the worksheet',
              'due_at': '2026-04-12T18:00:00Z',
              'total_points': 20,
            },
          ],
          nextCursor: 'cursor-2',
          hasMore: true,
        ),
      );

      final page = await repository.getAssignments(courseId: 'course-1');

      expect(page.items.single.id, 'assignment-1');
      expect(page.nextCursor, 'cursor-2');
      expect(page.hasMore, isTrue);
    });
  });
}
