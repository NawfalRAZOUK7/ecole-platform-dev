/// Invoice repository implementation — offline-first with cache.
///
/// Reference: S-100, DEC-E2-020 — Invoices 10min TTL

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/domain/entities/invoice.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/invoice_repository.dart';

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
}
