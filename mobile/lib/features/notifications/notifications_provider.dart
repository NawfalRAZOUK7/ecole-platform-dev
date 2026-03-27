/// Notifications state management — Riverpod provider for Phase 13.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/notification_item.dart';

class NotificationsState {
  final List<NotificationItem> items;
  final bool isLoading;
  final bool isRefreshing;
  final bool isLoadingMore;
  final String? error;
  final String? nextCursor;
  final bool hasMore;
  final String selectedCategory;
  final int unreadCount;

  const NotificationsState({
    this.items = const [],
    this.isLoading = false,
    this.isRefreshing = false,
    this.isLoadingMore = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
    this.selectedCategory = '',
    this.unreadCount = 0,
  });

  NotificationsState copyWith({
    List<NotificationItem>? items,
    bool? isLoading,
    bool? isRefreshing,
    bool? isLoadingMore,
    String? error,
    bool clearError = false,
    String? nextCursor,
    bool? hasMore,
    String? selectedCategory,
    int? unreadCount,
  }) {
    return NotificationsState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      isRefreshing: isRefreshing ?? this.isRefreshing,
      isLoadingMore: isLoadingMore ?? this.isLoadingMore,
      error: clearError ? null : (error ?? this.error),
      nextCursor: nextCursor ?? this.nextCursor,
      hasMore: hasMore ?? this.hasMore,
      selectedCategory: selectedCategory ?? this.selectedCategory,
      unreadCount: unreadCount ?? this.unreadCount,
    );
  }
}

class NotificationsNotifier extends StateNotifier<NotificationsState> {
  final Ref _ref;

  NotificationsNotifier(this._ref)
      : super(const NotificationsState(isLoading: true)) {
    load();
  }

  Future<void> load({bool refresh = false}) async {
    state = state.copyWith(
      isLoading: !refresh,
      isRefreshing: refresh,
      clearError: true,
    );
    try {
      final repo = _ref.read(notificationRepositoryProvider);
      final result = await repo.getNotifications(
        category: state.selectedCategory.isEmpty ? null : state.selectedCategory,
      );
      int unreadCount = state.unreadCount;
      try {
        unreadCount = await repo.getUnreadCount();
      } catch (_) {
        unreadCount = result.items.where((item) => !item.isRead).length;
      }
      state = state.copyWith(
        items: result.items,
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
        unreadCount: unreadCount,
        isLoading: false,
        isRefreshing: false,
      );
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        isRefreshing: false,
        error: e.toString(),
      );
    }
  }

  Future<void> loadMore() async {
    if (!state.hasMore || state.nextCursor == null || state.isLoadingMore) return;
    state = state.copyWith(isLoadingMore: true, clearError: true);
    try {
      final repo = _ref.read(notificationRepositoryProvider);
      final result = await repo.getNotifications(
        cursor: state.nextCursor,
        category: state.selectedCategory.isEmpty ? null : state.selectedCategory,
      );
      state = state.copyWith(
        items: [...state.items, ...result.items],
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
        isLoadingMore: false,
      );
    } catch (e) {
      state = state.copyWith(isLoadingMore: false, error: e.toString());
    }
  }

  Future<void> refresh() async {
    await _ref.read(cacheStoreProvider).invalidatePrefix('notifications:');
    await load(refresh: true);
  }

  Future<void> setCategory(String category) async {
    state = state.copyWith(selectedCategory: category, nextCursor: null, hasMore: false);
    await load();
  }

  Future<void> markRead(NotificationItem notification, {required bool read}) async {
    final repo = _ref.read(notificationRepositoryProvider);
    await repo.markRead(notification.id, read: read);
    final newUnreadCount = read
        ? (state.unreadCount > 0 ? state.unreadCount - 1 : 0)
        : state.unreadCount + 1;
    state = state.copyWith(
      unreadCount: newUnreadCount,
      items: state.items
          .map((item) => item.id == notification.id
              ? item.copyWith(
                  isRead: read,
                  readAt: read ? DateTime.now().toIso8601String() : null,
                )
              : item)
          .toList(),
    );
  }

  Future<void> deleteNotification(NotificationItem notification) async {
    final repo = _ref.read(notificationRepositoryProvider);
    await repo.deleteNotification(notification.id);
    state = state.copyWith(
      unreadCount: notification.isRead
          ? state.unreadCount
          : (state.unreadCount > 0 ? state.unreadCount - 1 : 0),
      items: state.items.where((item) => item.id != notification.id).toList(),
    );
  }

  Future<void> refreshBadge() async {
    try {
      final count =
          await _ref.read(notificationRepositoryProvider).getUnreadCount();
      state = state.copyWith(unreadCount: count);
    } catch (_) {
      // Ignore transient badge refresh failures.
    }
  }
}

final notificationsProvider =
    StateNotifierProvider<NotificationsNotifier, NotificationsState>((ref) {
  return NotificationsNotifier(ref);
});
