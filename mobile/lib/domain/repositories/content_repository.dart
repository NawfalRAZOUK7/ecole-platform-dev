/// Content repository interface — domain layer contract.
import '../entities/content_item.dart';
import 'feed_repository.dart'; // for PaginatedList

abstract class ContentRepository {
  /// Fetch content items with cursor pagination and optional filters.
  Future<PaginatedList<ContentItem>> getContentItems({
    String? cursor,
    String? contentType,
    String? levelBand,
  });
}
