import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/data/repositories_impl/communication/notification_repository_impl.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  test('lists notifications from the API and caches them', () async {
    final api = MockApiClient();
    final cache = MockCacheStore();
    final store = MockNotificationsStore();
    final repository = NotificationRepositoryImpl(
      api: api,
      cache: cache,
      notificationsStore: store,
    );

    when(() => cache.get('notifications:first:all:all')).thenAnswer(
      (_) async => null,
    );
    when(
      () => api.list('/notifications', params: <String, dynamic>{}),
    ).thenAnswer(
      (_) async => listResponse(
        const [
          {
            'id': 'notification-1',
            'school_id': 'school-1',
            'user_id': 'user-1',
            'title': 'Attendance update',
            'body': 'Student marked present',
            'category': 'attendance',
            'priority': 'normal',
            'created_at': '2026-04-10T08:00:00Z',
            'channels': ['in_app'],
          },
        ],
      ),
    );
    when(
      () => cache.put(any(), any(), any()),
    ).thenAnswer((_) async {});
    when(() => store.replaceAll(any())).thenAnswer((_) async {});

    final notifications = await repository.getNotifications();

    expect(notifications.items, hasLength(1));
    expect(notifications.items.single.title, 'Attendance update');
    verify(() => store.replaceAll(any())).called(1);
  });

  test('markRead updates local store and invalidates cached pages', () async {
    final api = MockApiClient();
    final cache = MockCacheStore();
    final store = MockNotificationsStore();
    final repository = NotificationRepositoryImpl(
      api: api,
      cache: cache,
      notificationsStore: store,
    );

    when(
      () => api.patch(
        '/notifications/notification-1/read',
        body: const {'read': true},
      ),
    ).thenAnswer((_) async => response(const {'ok': true}));
    when(() => store.readAll()).thenAnswer(
      (_) async => [
        {
          'id': 'notification-1',
          'school_id': 'school-1',
          'user_id': 'user-1',
          'title': 'Attendance update',
          'body': 'Student marked present',
          'category': 'attendance',
          'priority': 'normal',
          'created_at': '2026-04-10T08:00:00Z',
          'channels': ['in_app'],
          'is_read': false,
        },
      ],
    );
    when(() => store.replaceAll(any())).thenAnswer((_) async {});
    when(
      () => cache.invalidatePrefix('notifications:'),
    ).thenAnswer((_) async {});

    await repository.markRead('notification-1', read: true);

    verify(() => store.replaceAll(any())).called(1);
    verify(() => cache.invalidatePrefix('notifications:')).called(1);
  });

  test('loads unread counts', () async {
    final api = MockApiClient();
    final repository = NotificationRepositoryImpl(
      api: api,
      cache: MockCacheStore(),
      notificationsStore: MockNotificationsStore(),
    );

    when(() => api.get('/notifications/unread-count')).thenAnswer(
      (_) async => response(const {'unread_count': 4}),
    );

    final unreadCount = await repository.getUnreadCount();

    expect(unreadCount, 4);
  });
}
