/// Content state management — Riverpod provider.
///
/// Reference: S-098 — Content library with offline access

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/content_item.dart';

class ContentState {
  final List<ContentItem> items;
  final bool isLoading;
  final bool isLoadingMore;
  final String? error;
  final String? nextCursor;
  final bool hasMore;
  final String? typeFilter;
  final String? levelFilter;

  const ContentState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
    this.typeFilter,
    this.levelFilter,
  });
}

class ContentNotifier extends StateNotifier<ContentState> {
  final Ref _ref;

  ContentNotifier(this._ref) : super(const ContentState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = ContentState(
      isLoading: true,
      typeFilter: state.typeFilter,
      levelFilter: state.levelFilter,
    );
    try {
      final repo = _ref.read(contentRepositoryProvider);
      final result = await repo.getContentItems(
        contentType: state.typeFilter,
        levelBand: state.levelFilter,
      );
      state = ContentState(
        items: result.items,
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
        typeFilter: state.typeFilter,
        levelFilter: state.levelFilter,
      );
    } catch (e) {
      state = ContentState(
        error: e.toString(),
        typeFilter: state.typeFilter,
        levelFilter: state.levelFilter,
      );
    }
  }

  Future<void> loadMore() async {
    if (state.isLoadingMore || state.nextCursor == null) return;
    state = ContentState(
      items: state.items,
      isLoadingMore: true,
      nextCursor: state.nextCursor,
      hasMore: state.hasMore,
      typeFilter: state.typeFilter,
      levelFilter: state.levelFilter,
    );
    try {
      final repo = _ref.read(contentRepositoryProvider);
      final result = await repo.getContentItems(
        cursor: state.nextCursor,
        contentType: state.typeFilter,
        levelBand: state.levelFilter,
      );
      state = ContentState(
        items: [...state.items, ...result.items],
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
        typeFilter: state.typeFilter,
        levelFilter: state.levelFilter,
      );
    } catch (e) {
      state = ContentState(
        items: state.items,
        error: e.toString(),
        typeFilter: state.typeFilter,
        levelFilter: state.levelFilter,
      );
    }
  }

  void setTypeFilter(String? type) {
    state = ContentState(typeFilter: type, levelFilter: state.levelFilter);
    load();
  }

  void setLevelFilter(String? level) {
    state = ContentState(typeFilter: state.typeFilter, levelFilter: level);
    load();
  }

  Future<void> refresh() async {
    await _ref.read(cacheStoreProvider).invalidatePrefix('content:');
    await load();
  }
}

final contentProvider =
    StateNotifierProvider<ContentNotifier, ContentState>((ref) {
  return ContentNotifier(ref);
});
