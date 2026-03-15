/// Notification entity — user notification entry.
///
/// Maps to GET /notifications response (NotificationResponse schema).
class NotificationItem {
  final String id;
  final String schoolId;
  final String parentId;
  final String? eventRef;
  final String title;
  final String? body;
  final String createdAt;

  const NotificationItem({
    required this.id,
    required this.schoolId,
    required this.parentId,
    this.eventRef,
    required this.title,
    this.body,
    required this.createdAt,
  });
}
