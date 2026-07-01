/// Content repository interface — domain layer contract.
import 'package:ecole_platform/domain/entities/content/content_item.dart';
import 'package:ecole_platform/domain/common/pagination.dart';

abstract class ContentRepository {
  /// Fetch content items with cursor pagination and optional filters.
  /// [targetAge] is auto-injected by the backend for STD role based on DOB,
  /// but can be explicitly passed for library browsing.
  Future<PaginatedList<ContentItem>> getContentItems({
    String? cursor,
    String? contentType,
    String? levelBand,
    int? targetAge,
  });

  /// Fetch one content item by ID.
  Future<ContentItem> getContentItem(String contentItemId);

  /// Fetch ordered story pages for a content item.
  Future<List<ContentItemAsset>> getStoryPages(String contentItemId);

  /// Update progress for a content item.
  Future<void> updateProgress(String contentItemId, String status);
}
