/// Invoices state management — Riverpod provider.
///
/// Reference: S-100 — Invoice list with payment status

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/billing/invoice.dart';

class InvoicesState {
  final List<Invoice> items;
  final bool isLoading;
  final String? error;
  final String? nextCursor;
  final bool hasMore;
  final bool retrying;

  const InvoicesState({
    this.items = const [],
    this.isLoading = false,
    this.error,
    this.nextCursor,
    this.hasMore = false,
    this.retrying = false,
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

  Future<void> retryPayment(String invoiceId) async {
    state = InvoicesState(
      items: state.items,
      nextCursor: state.nextCursor,
      hasMore: state.hasMore,
      retrying: true,
    );
    try {
      final api = _ref.read(apiClientProvider);
      await api.post('/payments/initiate', body: {'invoice_id': invoiceId});
      await refresh();
    } catch (e) {
      state = InvoicesState(
        items: state.items,
        nextCursor: state.nextCursor,
        hasMore: state.hasMore,
        error: e.toString(),
      );
    }
  }
}

class InvoiceDetailData {
  final Invoice invoice;
  final List<InvoicePaymentRecord> payments;

  const InvoiceDetailData({
    required this.invoice,
    required this.payments,
  });
}

final invoiceDetailProvider =
    FutureProvider.family<InvoiceDetailData, String>((ref, invoiceId) async {
  final repository = ref.read(invoiceRepositoryProvider);
  final results = await Future.wait<dynamic>([
    repository.getInvoiceDetail(invoiceId),
    repository.getInvoicePayments(invoiceId),
  ]);
  return InvoiceDetailData(
    invoice: results[0] as Invoice,
    payments: results[1] as List<InvoicePaymentRecord>,
  );
});

final invoicesProvider =
    StateNotifierProvider<InvoicesNotifier, InvoicesState>((ref) {
  return InvoicesNotifier(ref);
});
