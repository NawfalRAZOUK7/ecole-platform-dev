/// Feed repository implementation — offline-first with cache.
///
/// Reference: S-096, DEC-E2-020 — Feed 5min TTL, pull-to-refresh invalidation

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/domain/entities/feed_item.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';

class FeedRepositoryImpl implements FeedRepository {
  final ApiClient _api;
  final CacheStore _cache;

  FeedRepositoryImpl({required ApiClient api, required CacheStore cache})
      : _api = api,
        _cache = cache;

  @override
  Future<PaginatedList<FeedItem>> getFeed({String? cursor}) async {
    final cacheKey = 'feed:${cursor ?? 'first'}';

    // Try cache first
    final cached = await _cache.get(cacheKey);
    if (cached != null) {
      return PaginatedList(
        items: cached.map(feedItemFromJson).toList(),
        hasMore: false, // cached pages don't track hasMore
      );
    }

    // Fetch from API
    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;

    final resp = await _api.list('/feed', params: params);

    // Cache the response
    await _cache.put(cacheKey, resp.data, CacheTtl.feed);

    return PaginatedList(
      items: resp.data.map(feedItemFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }
}
