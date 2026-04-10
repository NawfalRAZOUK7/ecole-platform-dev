/// Invoice repository implementation — offline-first with cache.
///
/// Reference: S-100, DEC-E2-020 — Invoices 10min TTL

import 'dart:io';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/invoice_repository.dart';
import 'package:path_provider/path_provider.dart';

class InvoiceRepositoryImpl implements InvoiceRepository {
  final ApiClient _api;
  final CacheStore _cache;

  InvoiceRepositoryImpl({required ApiClient api, required CacheStore cache})
      : _api = api,
        _cache = cache;

  @override
  Future<PaginatedList<Invoice>> getInvoices({String? cursor}) async {
    final cacheKey = 'invoices:${cursor ?? 'first'}';

    final cached = await _cache.get(cacheKey);
    if (cached != null) {
      return PaginatedList(
        items: cached.map(invoiceFromJson).toList(),
        hasMore: false,
      );
    }

    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;

    final resp = await _api.list('/invoices', params: params);
    await _cache.put(cacheKey, resp.data, CacheTtl.invoices);

    return PaginatedList(
      items: resp.data.map(invoiceFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }

  @override
  Future<Invoice> getInvoiceDetail(String id) async {
    final response = await _api.get('/invoices/$id');
    return invoiceFromJson(response.data);
  }

  @override
  Future<InvoicePaymentRecord> createPayment({
    required String invoiceId,
    required double amount,
    required String method,
  }) async {
    final response = await _api.post('/payments/initiate', body: {
      'invoice_id': invoiceId,
      'amount': amount,
      'method': method,
    });
    await _cache.invalidatePrefix('invoices:');
    return invoicePaymentFromJson(response.data);
  }

  @override
  Future<void> uploadPaymentProof({
    required String paymentId,
    required File file,
  }) async {
    await _api.uploadFile('/payments/$paymentId/proof', file: file);
  }

  @override
  Future<List<InvoicePaymentRecord>> getInvoicePayments(String invoiceId) async {
    final response = await _api.list('/payments/$invoiceId');
    return response.data.map(invoicePaymentFromJson).toList();
  }

  @override
  Future<File> downloadInvoicePdf(String invoiceId) async {
    final directory = await getTemporaryDirectory();
    final savePath = '${directory.path}/invoice-$invoiceId.pdf';
    return _api.download('/invoices/$invoiceId/pdf', savePath: savePath);
  }
}
