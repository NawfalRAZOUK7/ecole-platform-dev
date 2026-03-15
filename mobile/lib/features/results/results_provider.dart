/// Results state management — Riverpod provider.
///
/// Reference: S-099 — Student grades with offline cache

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/result.dart';

class ResultsState {
  final List<Result> items;
  final bool isLoading;
  final String? error;
  final String? nextCursor;
  final bool hasMore;

  const ResultsState({
    this.items = const [],
    this.isLoading = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
  });
}

class ResultsNotifier extends StateNotifier<ResultsState> {
  final Ref _ref;

  ResultsNotifier(this._ref) : super(const ResultsState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const ResultsState(isLoading: true);
    try {
      final repo = _ref.read(resultRepositoryProvider);
      final result = await repo.getResults();
      state = ResultsState(
        items: result.items,
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
      );
    } catch (e) {
      state = ResultsState(error: e.toString());
    }
  }

  Future<void> refresh() async {
    await _ref.read(cacheStoreProvider).invalidatePrefix('results:');
    await load();
  }
}

final resultsProvider =
    StateNotifierProvider<ResultsNotifier, ResultsState>((ref) {
  return ResultsNotifier(ref);
});
