/// Content repository implementation — offline-first with cache.
///
/// Reference: S-098, DEC-E2-020 — Content 15min TTL

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/domain/entities/content_item.dart';
import 'package:ecole_platform/domain/repositories/content_repository.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';

class ContentRepositoryImpl implements ContentRepository {
  final ApiClient _api;
  final CacheStore _cache;

  ContentRepositoryImpl({required ApiClient api, required CacheStore cache})
      : _api = api,
        _cache = cache;

  @override
  Future<PaginatedList<ContentItem>> getContentItems({
    String? cursor,
    String? contentType,
    String? levelBand,
  }) async {
    final cacheKey =
        'content:${cursor ?? 'first'}:${contentType ?? ''}:${levelBand ?? ''}';

    final cached = await _cache.get(cacheKey);
    if (cached != null) {
      return PaginatedList(
        items: cached.map(contentItemFromJson).toList(),
        hasMore: false,
      );
    }

    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;
    if (contentType != null) params['content_type'] = contentType;
    if (levelBand != null) params['level_band'] = levelBand;

    final resp = await _api.list('/content-items', params: params);
    await _cache.put(cacheKey, resp.data, CacheTtl.contentItems);

    return PaginatedList(
      items: resp.data.map(contentItemFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }
}
