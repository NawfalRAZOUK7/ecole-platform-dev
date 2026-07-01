/// Notification repository interface — domain layer contract.
import 'package:ecole_platform/domain/entities/communication/notification_item.dart';
import 'package:ecole_platform/domain/entities/communication/notification_settings.dart';
import 'package:ecole_platform/domain/common/pagination.dart';

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
