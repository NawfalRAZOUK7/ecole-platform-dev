/// Notification repository implementation — offline-first with cache.
///
/// Reference: S-097, DEC-E2-020 — Notifications 2min TTL

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/domain/entities/notification_item.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/notification_repository.dart';

class NotificationRepositoryImpl implements NotificationRepository {
  final ApiClient _api;
  final CacheStore _cache;

  NotificationRepositoryImpl({required ApiClient api, required CacheStore cache})
      : _api = api,
        _cache = cache;

  @override
  Future<PaginatedList<NotificationItem>> getNotifications({String? cursor}) async {
    final cacheKey = 'notifications:${cursor ?? 'first'}';

    final cached = await _cache.get(cacheKey);
    if (cached != null) {
      return PaginatedList(
        items: cached.map(notificationFromJson).toList(),
        hasMore: false,
      );
    }

    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;

    final resp = await _api.list('/notifications', params: params);
    await _cache.put(cacheKey, resp.data, CacheTtl.notifications);

    return PaginatedList(
      items: resp.data.map(notificationFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }
}
