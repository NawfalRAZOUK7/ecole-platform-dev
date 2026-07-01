/// Feed repository interface — domain layer contract for feed data.
import 'package:ecole_platform/domain/common/pagination.dart';
import 'package:ecole_platform/domain/entities/content/feed_item.dart';

abstract class FeedRepository {
  /// Fetch feed items with cursor pagination.
  Future<PaginatedList<FeedItem>> getFeed({String? cursor});
}
