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

  /// Fetch one content item by ID.
  Future<ContentItem> getContentItem(String contentItemId);

  /// Fetch ordered story pages for a content item.
  Future<List<ContentItemAsset>> getStoryPages(String contentItemId);

  /// Update progress for a content item.
  Future<void> updateProgress(String contentItemId, String status);
}
