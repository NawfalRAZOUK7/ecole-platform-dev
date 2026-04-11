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
  Future<List<InvoicePaymentRecord>> getInvoicePayments(
      String invoiceId) async {
    final response = await _api.list('/payments/$invoiceId');
    return response.data.map(invoicePaymentFromJson).toList();
  }

  @override
  Future<File> downloadInvoicePdf(String invoiceId) async {
    final directory = await getTemporaryDirectory();
    final savePath = '${directory.path}/invoice-$invoiceId.pdf';
    return _api.download('/invoices/$invoiceId/pdf', savePath: savePath);
  }

  @override
  Future<SiblingPolicy> getSiblingPolicy() async {
    final response = await _api.get('/billing/sibling-policy');
    return siblingPolicyFromJson(response.data);
  }

  @override
  Future<SiblingPolicy> updateSiblingPolicy({
    required List<SiblingDiscountTier> discounts,
    required int maxSiblingsCovered,
  }) async {
    final response = await _api.put(
      '/billing/sibling-policy',
      body: {
        'discounts': discounts
            .map((item) => {
                  'sibling_rank': item.siblingRank,
                  'discount_percent': item.discountPercent,
                })
            .toList(),
        'max_siblings_covered': maxSiblingsCovered,
      },
    );
    return siblingPolicyFromJson(response.data);
  }

  @override
  Future<LateFeePolicy> getLateFeePolicy() async {
    final response = await _api.get('/billing/late-fee-policy');
    return lateFeePolicyFromJson(response.data);
  }

  @override
  Future<LateFeePolicy> updateLateFeePolicy({
    required int gracePeriodDays,
    required double feePercent,
    required double maxFeeCap,
  }) async {
    final response = await _api.put(
      '/billing/late-fee-policy',
      body: {
        'grace_period_days': gracePeriodDays,
        'fee_percent': feePercent,
        'max_fee_cap': maxFeeCap,
      },
    );
    return lateFeePolicyFromJson(response.data);
  }

  @override
  Future<List<PaymentPlan>> listPaymentPlans({String? status}) async {
    final response = await _api.list(
      '/billing/payment-plans',
      params: status == null || status.isEmpty ? null : {'status': status},
    );
    return response.data.map(paymentPlanFromJson).toList();
  }

  @override
  Future<PaymentPlan> getPaymentPlan(String id) async {
    final response = await _api.get('/billing/payment-plans/$id');
    return paymentPlanFromJson(response.data);
  }

  @override
  Future<PaymentPlan> createPaymentPlan({
    required String studentId,
    required String name,
    required double totalAmount,
    required String startDate,
    required List<PaymentPlanDraftInstallment> installments,
  }) async {
    final response = await _api.post(
      '/billing/payment-plans',
      body: {
        'student_id': studentId,
        'name': name,
        'total_amount': totalAmount,
        'start_date': startDate,
        'installments': installments
            .map((item) => {
                  'due_date': item.dueDate,
                  'amount': item.amount,
                })
            .toList(),
      },
    );
    await _cache.invalidatePrefix('invoices:');
    return paymentPlanFromJson(response.data);
  }
}
