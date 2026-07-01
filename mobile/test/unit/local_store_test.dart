import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/core/storage/attendance_store.dart';
import 'package:ecole_platform/core/storage/cache_store.dart';
import 'package:ecole_platform/core/storage/database.dart';
import 'package:ecole_platform/core/storage/documents_store.dart';
import 'package:ecole_platform/core/storage/events_store.dart';
import 'package:ecole_platform/core/storage/notifications_store.dart';
import 'package:ecole_platform/core/storage/offline_queue.dart';
import 'package:ecole_platform/core/storage/quiz_offline_store.dart';
import 'package:ecole_platform/core/storage/reports_store.dart';

import '../helpers/test_database.dart';
import '../helpers/test_mocks.dart';

void main() {
  group('Local stores', () {
    setUpAll(() async {
      await initializeTestDatabase();
      registerTestFallbacks();
    });

    setUp(() async {
      await resetTestDatabase();
    });

    group('CacheStore', () {
      test('reads back non-expired cached data', () async {
        final store = CacheStore();

        await store.put(
          'feed:first',
          const [
            {'id': 'feed-1', 'title': 'Important update'},
          ],
          60,
        );

        final cached = await store.get('feed:first');

        expect(cached, isNotNull);
        expect(cached, hasLength(1));
        expect(cached!.first['id'], 'feed-1');
      });

      test('drops expired cached data on read', () async {
        final store = CacheStore();
        final db = await AppDatabase.instance;

        await store.put(
          'notifications:first',
          const [
            {'id': 'n-1'},
          ],
          1,
        );
        await db.update(
          'cache_entries',
          {'created_at': 0},
          where: 'cache_key = ?',
          whereArgs: ['notifications:first'],
        );

        final cached = await store.get('notifications:first');
        final rows = await db.query(
          'cache_entries',
          where: 'cache_key = ?',
          whereArgs: ['notifications:first'],
        );

        expect(cached, isNull);
        expect(rows, isEmpty);
      });

      test('invalidates key prefixes and prunes expired rows', () async {
        final store = CacheStore();
        final db = await AppDatabase.instance;

        await store.put(
          'feed:first',
          const [
            {'id': 'f-1'},
          ],
          60,
        );
        await store.put(
          'feed:second',
          const [
            {'id': 'f-2'},
          ],
          60,
        );
        await store.put(
          'results:first',
          const [
            {'id': 'r-1'},
          ],
          1,
        );
        await db.update(
          'cache_entries',
          {'created_at': 0},
          where: 'cache_key = ?',
          whereArgs: ['results:first'],
        );

        await store.invalidatePrefix('feed:');
        await store.pruneExpired();

        expect(await store.get('feed:first'), isNull);
        expect(await store.get('feed:second'), isNull);
        expect(await store.get('results:first'), isNull);
      });
    });

    group('OfflineQueue', () {
      test('enqueues commands and marks them completed', () async {
        final queue = OfflineQueue();

        final id = await queue.enqueue(
          method: 'POST',
          path: '/attendance/class/class-1',
          body: const {'status': 'present'},
        );

        final pending = await queue.getPending();
        expect(pending, hasLength(1));
        expect(await queue.pendingCount(), 1);
        expect(pending.single.id, id);
        expect(pending.single.bodyJson, {'status': 'present'});

        await queue.markCompleted(id);

        expect(await queue.pendingCount(), 0);
        expect(await queue.getAll(), isEmpty);
      });

      test('tracks failed commands and allows reset to pending', () async {
        final queue = OfflineQueue();

        final id = await queue.enqueue(
          method: 'PATCH',
          path: '/notifications/n-1/read',
        );

        await queue.markFailed(id, 'timeout');

        final failed = await queue.getFailed();
        expect(failed, hasLength(1));
        expect(failed.single.lastError, 'timeout');
        expect(failed.single.retryCount, 1);
        expect(await queue.failedCount(), 1);

        await queue.resetToPending(id);

        expect(await queue.failedCount(), 0);
        expect(await queue.pendingCount(), 1);
      });
    });

    group('NotificationsStore', () {
      test('keeps only the latest 100 notifications on replaceAll', () async {
        final store = NotificationsStore();
        final items = List.generate(
          120,
          (index) => {
            'id': 'notification-$index',
            'title': 'Notification $index',
          },
        );

        await store.replaceAll(items);

        final cached = await store.readAll();
        expect(cached, hasLength(100));
      });
    });

    group('ReportsStore', () {
      test('upserts, reads by id, and trims the cache to five items', () async {
        final store = ReportsStore();

        for (var index = 0; index < 7; index += 1) {
          await store.upsert(
            {
              'id': 'report-$index',
              'type': 'student_report_card',
              'status': 'ready',
              'created_at': '2026-04-10T08:00:00Z',
            },
            filePath: '/tmp/report-$index.pdf',
          );
        }

        final cached = await store.readAll();
        final report = await store.readById('report-6');

        expect(cached, hasLength(5));
        expect(report, isNotNull);
        expect(report!['local_file_path'], '/tmp/report-6.pdf');
      });
    });

    group('EventsStore', () {
      test('stores month events and trims old month buckets', () async {
        final store = EventsStore();

        for (final month in const [
          '2026-01',
          '2026-02',
          '2026-03',
          '2026-04',
        ]) {
          await store.replaceMonth(
            month,
            [
              {
                'id': 'event-$month',
                'instance_id': 'instance-$month',
                'start_at': '$month-01T08:00:00Z',
              },
            ],
          );
        }

        final db = await AppDatabase.instance;
        final rows = await db.rawQuery('''
          SELECT DISTINCT cache_month
          FROM cached_calendar_events
        ''');

        expect(rows, hasLength(3));
      });
    });

    group('DocumentsStore', () {
      test('replaces documents and attaches offline file paths', () async {
        final store = DocumentsStore();

        await store.replaceDocuments(
          'documents:mine',
          const [
            {
              'id': 'document-1',
              'original_filename': 'bulletin.pdf',
            },
          ],
        );
        await store.attachDocumentFile('document-1', '/tmp/bulletin.pdf');

        final documents = await store.readDocuments('documents:mine');

        expect(documents, hasLength(1));
        expect(documents.single['local_file_path'], '/tmp/bulletin.pdf');
      });

      test('replaces checklist entries for a student', () async {
        final store = DocumentsStore();

        await store.replaceChecklist(
          'student-1',
          const [
            {
              'category': 'report_card',
              'status': 'uploaded',
            },
          ],
        );

        final checklist = await store.readChecklist('student-1');

        expect(checklist, hasLength(1));
        expect(checklist.single['category'], 'report_card');
      });

      test('replaces resources and attaches offline file paths', () async {
        final store = DocumentsStore();

        await store.replaceResources(
          'resources|math',
          const [
            {
              'id': 'resource-1',
              'title': 'Math pack',
            },
          ],
        );
        await store.attachResourceFile('resource-1', '/tmp/math-pack.pdf');

        final resources = await store.readResources('resources|math');

        expect(resources, hasLength(1));
        expect(resources.single['local_file_path'], '/tmp/math-pack.pdf');
      });
    });

    group('QuizOfflineStore', () {
      test('caches quiz questions and manages draft answers', () async {
        final store = QuizOfflineStore();

        await store.cacheQuizQuestions(
          'quiz-1',
          const [
            {
              'id': 'question-1',
              'question_type': 'MCQ',
              'question_text': 'What is 2 + 2?',
            },
          ],
        );
        await store.saveDraftAnswers(
          'attempt-1',
          const {'question-1': 'B'},
        );

        expect(await store.getCachedQuestions('quiz-1'), hasLength(1));
        expect(await store.getCachedQuizIds(), contains('quiz-1'));
        expect(await store.getDraftAnswers('attempt-1'), {'question-1': 'B'});

        await store.clearDraft('attempt-1');

        expect(await store.getDraftAnswers('attempt-1'), isNull);
      });
    });

    group('AttendanceStore', () {
      test('delegates attendance keys to the underlying cache store', () async {
        final cache = MockCacheStore();
        final store = AttendanceStore(cache: cache);

        when(() => cache.put(any(), any(), any())).thenAnswer((_) async {});
        when(() => cache.get(any())).thenAnswer(
          (_) async => const [
            {'id': 'entry-1'},
          ],
        );
        when(() => cache.invalidatePrefix(any())).thenAnswer((_) async {});

        await store.writeClassAttendance(
          'class-1',
          '2026-04-11',
          const [
            {'id': 'entry-1'},
          ],
        );
        final records =
            await store.readClassAttendance('class-1', '2026-04-11');
        await store.invalidateClass('class-1');

        expect(records, isNotNull);
        verify(
          () => cache.put(
            'attendance:class:class-1:2026-04-11',
            const [
              {'id': 'entry-1'},
            ],
            CacheTtl.attendance,
          ),
        ).called(1);
        verify(
          () => cache.get('attendance:class:class-1:2026-04-11'),
        ).called(1);
        verify(
          () => cache.invalidatePrefix('attendance:class:class-1'),
        ).called(1);
      });
    });
  });
}
