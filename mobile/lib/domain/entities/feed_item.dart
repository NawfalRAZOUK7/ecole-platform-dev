/// Feed item entity — parent news feed entry.
///
/// Maps to GET /feed response (FeedItemResponse schema).
class FeedItem {
  final String id;
  final String schoolId;
  final String parentId;
  final String? studentId;
  final String sourceType;
  final String? sourceRef;
  final String title;
  final String? body;
  final String createdAt;

  const FeedItem({
    required this.id,
    required this.schoolId,
    required this.parentId,
    this.studentId,
    required this.sourceType,
    this.sourceRef,
    required this.title,
    this.body,
    required this.createdAt,
  });
}
