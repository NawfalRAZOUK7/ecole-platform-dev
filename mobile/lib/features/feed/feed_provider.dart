/// Feed state management — Riverpod provider.
///
/// Reference: S-096 — Parent feed with offline-first cache

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/feed_item.dart';

class FeedState {
  final List<FeedItem> items;
  final bool isLoading;
  final bool isLoadingMore;
  final String? error;
  final String? nextCursor;
  final bool hasMore;

  const FeedState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
  });
}

class FeedNotifier extends StateNotifier<FeedState> {
  final Ref _ref;

  FeedNotifier(this._ref) : super(const FeedState(isLoading: true)) {
    loadFeed();
  }

  Future<void> loadFeed() async {
    state = const FeedState(isLoading: true);
    try {
      final repo = _ref.read(feedRepositoryProvider);
      final result = await repo.getFeed();
      state = FeedState(
        items: result.items,
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
      );
    } catch (e) {
      state = FeedState(error: e.toString());
    }
  }

  Future<void> loadMore() async {
    if (state.isLoadingMore || state.nextCursor == null) return;
    state = FeedState(
      items: state.items,
      isLoadingMore: true,
      nextCursor: state.nextCursor,
      hasMore: state.hasMore,
    );
    try {
      final repo = _ref.read(feedRepositoryProvider);
      final result = await repo.getFeed(cursor: state.nextCursor);
      state = FeedState(
        items: [...state.items, ...result.items],
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
      );
    } catch (e) {
      state = FeedState(
        items: state.items,
        error: e.toString(),
      );
    }
  }

  Future<void> refresh() async {
    // Invalidate cache and reload
    await _ref.read(cacheStoreProvider).invalidatePrefix('feed:');
    await loadFeed();
  }
}

final feedProvider = StateNotifierProvider<FeedNotifier, FeedState>((ref) {
  return FeedNotifier(ref);
});
