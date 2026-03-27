/// Notification repository interface — domain layer contract.
import '../entities/notification_item.dart';
import '../entities/notification_settings.dart';
import 'feed_repository.dart'; // for PaginatedList

abstract class NotificationRepository {
  /// Fetch notifications with cursor pagination.
  Future<PaginatedList<NotificationItem>> getNotifications({
    String? cursor,
    String? category,
    bool? read,
  });

  Future<void> markRead(String notificationId, {required bool read});

  Future<void> deleteNotification(String notificationId);

  Future<int> getUnreadCount();

  Future<List<NotificationPreferenceItem>> getPreferences();

  Future<void> updatePreferences(List<NotificationPreferenceItem> preferences);

  Future<String> getDigestFrequency();

  Future<void> updateDigestFrequency(String digestFrequency);

  Future<List<RegisteredDevice>> getDevices();

  Future<void> removeDevice(String deviceId);
}
