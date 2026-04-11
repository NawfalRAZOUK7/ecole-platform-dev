/// My Children state management — Riverpod provider.
///
/// Phase 5C-patch: Parent's linked children list.

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/child_link.dart';

class MyChildrenState {
  final List<ChildLink> items;
  final bool isLoading;
  final String? error;

  const MyChildrenState({
    this.items = const [],
    this.isLoading = false,
    this.error,
  });
}

class MyChildrenNotifier extends StateNotifier<MyChildrenState> {
  final Ref _ref;

  MyChildrenNotifier(this._ref)
      : super(const MyChildrenState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const MyChildrenState(isLoading: true);
    try {
      final repo = _ref.read(authRepositoryProvider);
      final children = await repo.getChildren();
      state = MyChildrenState(items: children);
    } catch (e) {
      state = MyChildrenState(error: e.toString());
    }
  }

  Future<void> refresh() async {
    await load();
  }
}

final myChildrenProvider =
    StateNotifierProvider<MyChildrenNotifier, MyChildrenState>((ref) {
  return MyChildrenNotifier(ref);
});
