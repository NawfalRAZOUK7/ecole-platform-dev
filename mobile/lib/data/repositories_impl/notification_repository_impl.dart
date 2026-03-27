/// Notification repository implementation — API + offline cache.

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/data/local_store/notifications_store.dart';
import 'package:ecole_platform/domain/entities/notification_item.dart';
import 'package:ecole_platform/domain/entities/notification_settings.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/notification_repository.dart';

class NotificationRepositoryImpl implements NotificationRepository {
  final ApiClient _api;
  final CacheStore _cache;
  final NotificationsStore _notificationsStore;

  NotificationRepositoryImpl({
    required ApiClient api,
    required CacheStore cache,
    required NotificationsStore notificationsStore,
  })  : _api = api,
        _cache = cache,
        _notificationsStore = notificationsStore;

  @override
  Future<PaginatedList<NotificationItem>> getNotifications({
    String? cursor,
    String? category,
    bool? read,
  }) async {
    final cacheKey =
        'notifications:${cursor ?? 'first'}:${category ?? 'all'}:${read?.toString() ?? 'all'}';

    final cached = await _cache.get(cacheKey);
    if (cached != null) {
      return PaginatedList(
        items: cached.map(notificationFromJson).toList(),
        hasMore: false,
      );
    }

    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;
    if (category != null && category.isNotEmpty) params['category'] = category;
    if (read != null) params['read'] = read.toString();

    try {
      final resp = await _api.list('/notifications', params: params);
      await _cache.put(cacheKey, resp.data, CacheTtl.notifications);

      if (cursor == null && category == null && read == null) {
        await _notificationsStore.replaceAll(resp.data);
      }

      return PaginatedList(
        items: resp.data.map(notificationFromJson).toList(),
        nextCursor: resp.nextCursor,
        hasMore: resp.hasMore,
      );
    } on ApiClientError {
      if (cursor == null && category == null && read == null) {
        final offline = await _notificationsStore.readAll();
        return PaginatedList(
          items: offline.map(notificationFromJson).toList(),
          hasMore: false,
        );
      }
      rethrow;
    }
  }

  @override
  Future<void> markRead(String notificationId, {required bool read}) async {
    await _api.patch('/notifications/$notificationId/read', body: {'read': read});
    final cached = await _notificationsStore.readAll();
    final updated = cached
        .map((item) => item['id'] == notificationId
            ? {
                ...item,
                'is_read': read,
                'read_at': read ? DateTime.now().toIso8601String() : null,
              }
            : item)
        .toList();
    await _notificationsStore.replaceAll(updated);
    await _cache.invalidatePrefix('notifications:');
  }

  @override
  Future<void> deleteNotification(String notificationId) async {
    await _api.delete('/notifications/$notificationId');
    await _notificationsStore.remove(notificationId);
    await _cache.invalidatePrefix('notifications:');
  }

  @override
  Future<int> getUnreadCount() async {
    final resp = await _api.get('/notifications/unread-count');
    return resp.data['unread_count'] as int? ?? 0;
  }

  @override
  Future<List<NotificationPreferenceItem>> getPreferences() async {
    final resp = await _api.get('/notifications/preferences');
    final prefs = (resp.data['preferences'] as List<dynamic>? ?? const [])
        .cast<Map<String, dynamic>>();
    return prefs.map(notificationPreferenceFromJson).toList();
  }

  @override
  Future<void> updatePreferences(List<NotificationPreferenceItem> preferences) async {
    await _api.post(
      '/notifications/preferences',
      body: {
        'preferences': preferences
            .map((item) => {
                  'channel': item.channel,
                  'category': item.category,
                  'enabled': item.enabled,
                  'digest_frequency': item.digestFrequency,
                })
            .toList(),
      },
    );
  }

  @override
  Future<String> getDigestFrequency() async {
    final resp = await _api.get('/notifications/digest/preferences');
    return resp.data['digest_frequency'] as String? ?? 'off';
  }

  @override
  Future<void> updateDigestFrequency(String digestFrequency) async {
    await _api.post(
      '/notifications/digest/preferences',
      body: {'digest_frequency': digestFrequency},
    );
  }

  @override
  Future<List<RegisteredDevice>> getDevices() async {
    final resp = await _api.list('/devices');
    return resp.data.map(registeredDeviceFromJson).toList();
  }

  @override
  Future<void> removeDevice(String deviceId) async {
    await _api.delete('/devices/$deviceId');
  }
}
