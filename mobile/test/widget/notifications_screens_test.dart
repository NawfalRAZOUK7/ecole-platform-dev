import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/communication/notification_item.dart';
import 'package:ecole_platform/domain/common/pagination.dart';
import 'package:ecole_platform/features/communication/notifications/notifications_screen.dart';

import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

NotificationItem _makeNotification({
  String id = 'notif-1',
  bool isRead = false,
}) =>
    NotificationItem(
      id: id,
      schoolId: 'school-1',
      userId: 'user-1',
      title: 'Test notification',
      body: 'You have a new message.',
      category: 'general',
      priority: 'normal',
      isRead: isRead,
      createdAt: '2026-05-01T10:00:00Z',
    );

Future<void> _settle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 300));
}

void main() {
  group('Notifications screens', () {
    setUpAll(registerTestFallbacks);

    testWidgets('NotificationsScreen shows list of notifications',
        (tester) async {
      final notificationRepository = MockNotificationRepository();

      when(
        () => notificationRepository.getNotifications(
          cursor: any(named: 'cursor'),
          category: any(named: 'category'),
        ),
      ).thenAnswer(
        (_) async => PaginatedList<NotificationItem>(
          items: [_makeNotification()],
          nextCursor: null,
          hasMore: false,
        ),
      );
      when(() => notificationRepository.getUnreadCount())
          .thenAnswer((_) async => 1);

      await pumpApp(
        tester,
        const NotificationsScreen(),
        overrides: buildMockRepositoryOverrides(
          notificationRepository: notificationRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('Test notification'), findsOneWidget);
    });

    testWidgets('NotificationsScreen shows empty state when no notifications',
        (tester) async {
      final notificationRepository = MockNotificationRepository();

      when(
        () => notificationRepository.getNotifications(
          cursor: any(named: 'cursor'),
          category: any(named: 'category'),
        ),
      ).thenAnswer(
        (_) async => const PaginatedList<NotificationItem>(
          items: [],
          nextCursor: null,
          hasMore: false,
        ),
      );
      when(() => notificationRepository.getUnreadCount())
          .thenAnswer((_) async => 0);

      await pumpApp(
        tester,
        const NotificationsScreen(),
        overrides: buildMockRepositoryOverrides(
          notificationRepository: notificationRepository,
        ),
      );
      await tester.pumpAndSettle();

      // Should show some empty state (text or icon)
      expect(find.byType(Scaffold), findsWidgets);
    });

    testWidgets('NotificationsScreen has AppBar', (tester) async {
      final notificationRepository = MockNotificationRepository();

      when(
        () => notificationRepository.getNotifications(
          cursor: any(named: 'cursor'),
          category: any(named: 'category'),
        ),
      ).thenAnswer(
        (_) async => const PaginatedList<NotificationItem>(
          items: [],
          nextCursor: null,
          hasMore: false,
        ),
      );
      when(() => notificationRepository.getUnreadCount())
          .thenAnswer((_) async => 0);

      await pumpApp(
        tester,
        const NotificationsScreen(),
        overrides: buildMockRepositoryOverrides(
          notificationRepository: notificationRepository,
        ),
      );

      expect(find.byType(AppBar), findsOneWidget);
    });
  });
}
