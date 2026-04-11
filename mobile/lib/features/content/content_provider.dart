/// Content state management — Riverpod provider.
///
/// Reference: S-098 — Content library with offline access
/// Phase 5B: Added search + sort support.

import 'dart:async';

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
  final String search;
  final bool sortAscending;

  const ContentState({
    this.items = const [],
    this.isLoading = false,
    this.isLoadingMore = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
    this.typeFilter,
    this.levelFilter,
    this.search = '',
    this.sortAscending = true,
  });

  List<ContentItem> get filteredItems {
    var result = items;
    if (search.isNotEmpty) {
      final q = search.toLowerCase();
      result = result.where((i) => i.title.toLowerCase().contains(q)).toList();
    }
    if (sortAscending) {
      result.sort((a, b) => a.title.compareTo(b.title));
    } else {
      result.sort((a, b) => b.title.compareTo(a.title));
    }
    return result;
  }
}

class ContentNotifier extends StateNotifier<ContentState> {
  final Ref _ref;
  Timer? _debounce;

  ContentNotifier(this._ref) : super(const ContentState(isLoading: true)) {
    load();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  Future<void> load() async {
    state = ContentState(
      isLoading: true,
      typeFilter: state.typeFilter,
      levelFilter: state.levelFilter,
      search: state.search,
      sortAscending: state.sortAscending,
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
        search: state.search,
        sortAscending: state.sortAscending,
      );
    } catch (e) {
      state = ContentState(
        error: e.toString(),
        typeFilter: state.typeFilter,
        levelFilter: state.levelFilter,
        search: state.search,
        sortAscending: state.sortAscending,
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
      search: state.search,
      sortAscending: state.sortAscending,
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
        search: state.search,
        sortAscending: state.sortAscending,
      );
    } catch (e) {
      state = ContentState(
        items: state.items,
        error: e.toString(),
        typeFilter: state.typeFilter,
        levelFilter: state.levelFilter,
        search: state.search,
        sortAscending: state.sortAscending,
      );
    }
  }

  void setTypeFilter(String? type) {
    state = ContentState(
      typeFilter: type,
      levelFilter: state.levelFilter,
      search: state.search,
      sortAscending: state.sortAscending,
    );
    load();
  }

  void setLevelFilter(String? level) {
    state = ContentState(
      typeFilter: state.typeFilter,
      levelFilter: level,
      search: state.search,
      sortAscending: state.sortAscending,
    );
    load();
  }

  void setSearch(String value) {
    state = ContentState(
      items: state.items,
      typeFilter: state.typeFilter,
      levelFilter: state.levelFilter,
      search: value,
      sortAscending: state.sortAscending,
      nextCursor: state.nextCursor,
      hasMore: state.hasMore,
    );
  }

  void toggleSort() {
    state = ContentState(
      items: state.items,
      typeFilter: state.typeFilter,
      levelFilter: state.levelFilter,
      search: state.search,
      sortAscending: !state.sortAscending,
      nextCursor: state.nextCursor,
      hasMore: state.hasMore,
    );
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
