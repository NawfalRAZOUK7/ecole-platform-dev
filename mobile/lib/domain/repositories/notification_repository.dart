/// Notification repository interface — domain layer contract.
import '../entities/notification_item.dart';
import 'feed_repository.dart'; // for PaginatedList

abstract class NotificationRepository {
  /// Fetch notifications with cursor pagination.
  Future<PaginatedList<NotificationItem>> getNotifications({String? cursor});
}
