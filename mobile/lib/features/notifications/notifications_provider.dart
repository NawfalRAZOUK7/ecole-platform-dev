/// Notifications state management — Riverpod provider.
///
/// Reference: S-097 — Notification list with cache
/// Phase 5B: Added search support.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/notification_item.dart';

class NotificationsState {
  final List<NotificationItem> items;
  final bool isLoading;
  final bool isLoadingMore;
  final String? error;
  final String? nextCursor;
  final bool hasMore;
  final String search;

  const NotificationsState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
    this.search = '',
  });

  List<NotificationItem> get filteredItems {
    if (search.isEmpty) return items;
    final q = search.toLowerCase();
    return items
        .where((n) =>
            n.title.toLowerCase().contains(q) ||
            (n.body?.toLowerCase().contains(q) ?? false))
        .toList();
  }
}

class NotificationsNotifier extends StateNotifier<NotificationsState> {
  final Ref _ref;

  NotificationsNotifier(this._ref) : super(const NotificationsState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = NotificationsState(isLoading: true, search: state.search);
    try {
      final repo = _ref.read(notificationRepositoryProvider);
      final result = await repo.getNotifications();
      state = NotificationsState(
        items: result.items,
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
        search: state.search,
      );
    } catch (e) {
      state = NotificationsState(error: e.toString(), search: state.search);
    }
  }

  Future<void> loadMore() async {
    if (state.isLoadingMore || state.nextCursor == null) return;
    state = NotificationsState(
      items: state.items,
      isLoadingMore: true,
      nextCursor: state.nextCursor,
      hasMore: state.hasMore,
      search: state.search,
    );
    try {
      final repo = _ref.read(notificationRepositoryProvider);
      final result = await repo.getNotifications(cursor: state.nextCursor);
      state = NotificationsState(
        items: [...state.items, ...result.items],
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
        search: state.search,
      );
    } catch (e) {
      state = NotificationsState(
        items: state.items,
        error: e.toString(),
        search: state.search,
      );
    }
  }

  void setSearch(String value) {
    state = NotificationsState(
      items: state.items,
      nextCursor: state.nextCursor,
      hasMore: state.hasMore,
      search: value,
    );
  }

  Future<void> refresh() async {
    await _ref.read(cacheStoreProvider).invalidatePrefix('notifications:');
    await load();
  }
}

final notificationsProvider =
    StateNotifierProvider<NotificationsNotifier, NotificationsState>((ref) {
  return NotificationsNotifier(ref);
});
