/// Notification entity — user notification entry.
///
/// Maps to GET /notifications response (NotificationResponse schema).
class NotificationItem {
  final String id;
  final String schoolId;
  final String userId;
  final String? eventRef;
  final String title;
  final String? body;
  final String category;
  final String priority;
  final String? actionUrl;
  final Map<String, dynamic>? actionPayload;
  final bool isRead;
  final String? readAt;
  final String createdAt;
  final List<String> channels;

  const NotificationItem({
    required this.id,
    required this.schoolId,
    required this.userId,
    this.eventRef,
    required this.title,
    this.body,
    required this.category,
    required this.priority,
    this.actionUrl,
    this.actionPayload,
    this.isRead = false,
    this.readAt,
    required this.createdAt,
    this.channels = const [],
  });

  NotificationItem copyWith({
    String? id,
    String? schoolId,
    String? userId,
    String? eventRef,
    String? title,
    String? body,
    String? category,
    String? priority,
    String? actionUrl,
    Map<String, dynamic>? actionPayload,
    bool? isRead,
    String? readAt,
    String? createdAt,
    List<String>? channels,
  }) {
    return NotificationItem(
      id: id ?? this.id,
      schoolId: schoolId ?? this.schoolId,
      userId: userId ?? this.userId,
      eventRef: eventRef ?? this.eventRef,
      title: title ?? this.title,
      body: body ?? this.body,
      category: category ?? this.category,
      priority: priority ?? this.priority,
      actionUrl: actionUrl ?? this.actionUrl,
      actionPayload: actionPayload ?? this.actionPayload,
      isRead: isRead ?? this.isRead,
      readAt: readAt ?? this.readAt,
      createdAt: createdAt ?? this.createdAt,
      channels: channels ?? this.channels,
    );
  }
}
