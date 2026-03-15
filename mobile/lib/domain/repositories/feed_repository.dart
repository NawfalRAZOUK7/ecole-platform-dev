/// Feed repository interface — domain layer contract for feed data.
import '../entities/feed_item.dart';

/// Paginated list response with cursor.
class PaginatedList<T> {
  final List<T> items;
  final String? nextCursor;
  final bool hasMore;

  const PaginatedList({
    required this.items,
    this.nextCursor,
    required this.hasMore,
  });
}

abstract class FeedRepository {
  /// Fetch feed items with cursor pagination.
  Future<PaginatedList<FeedItem>> getFeed({String? cursor});
}
