/// Invoices state management — Riverpod provider.
///
/// Reference: S-100 — Invoice list with payment status

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';

class InvoicesState {
  final List<Invoice> items;
  final bool isLoading;
  final String? error;
  final String? nextCursor;
  final bool hasMore;

  const InvoicesState({
    this.items = const [],
    this.isLoading = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
  });
}

class InvoicesNotifier extends StateNotifier<InvoicesState> {
  final Ref _ref;

  InvoicesNotifier(this._ref) : super(const InvoicesState(isLoading: true)) {
    load();
  }

  Future<void> load() async {
    state = const InvoicesState(isLoading: true);
    try {
      final repo = _ref.read(invoiceRepositoryProvider);
      final result = await repo.getInvoices();
      state = InvoicesState(
        items: result.items,
        nextCursor: result.nextCursor,
        hasMore: result.hasMore,
      );
    } catch (e) {
      state = InvoicesState(error: e.toString());
    }
  }

  Future<void> refresh() async {
    await _ref.read(cacheStoreProvider).invalidatePrefix('invoices:');
    await load();
  }
}

final invoicesProvider =
    StateNotifierProvider<InvoicesNotifier, InvoicesState>((ref) {
  return InvoicesNotifier(ref);
});
