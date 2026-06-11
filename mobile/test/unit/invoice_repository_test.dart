import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/repositories_impl/billing/invoice_repository_impl.dart';
import 'package:ecole_platform/domain/common/pagination.dart';
import 'package:ecole_platform/domain/entities/billing/invoice.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

Map<String, dynamic> _invoiceJson(
        {String id = 'inv-1', String status = 'pending'}) =>
    {
      'id': id,
      'school_id': 'school-1',
      'parent_id': 'par-1',
      'period_id': 'p1',
      'invoice_number': 'INV-2026-001',
      'student_id': 'stu-1',
      'student_name': 'Alice',
      'label': 'Frais',
      'status': status,
      'total_amount': 3500.0,
      'currency': 'MAD',
      'issued_date': '2026-05-01',
      'due_date': '2026-05-31',
      'paid_at': null,
      'pdf_url': null,
      'line_items': <dynamic>[],
    };

Map<String, dynamic> _paymentJson({String id = 'pay-1'}) => {
      'id': id,
      'invoice_id': 'inv-1',
      'amount': 3500.0,
      'method': 'bank_transfer',
      'status': 'pending',
      'created_at': '2026-05-10T09:00:00Z',
      'finalized_at': null,
      'proof_url': null,
    };

void main() {
  late MockApiClient api;
  late MockCacheStore cache;
  late InvoiceRepositoryImpl repo;

  setUpAll(registerTestFallbacks);

  setUp(() {
    api = MockApiClient();
    cache = MockCacheStore();
    repo = InvoiceRepositoryImpl(api: api, cache: cache);
    when(() => cache.get(any())).thenAnswer((_) async => null);
    when(() => cache.put(any(), any(), any())).thenAnswer((_) async {});
    when(() => cache.invalidatePrefix(any())).thenAnswer((_) async {});
    when(() => cache.invalidate(any())).thenAnswer((_) async {});
  });

  group('getInvoices', () {
    test('returns paginated invoices from API on cache miss', () async {
      when(() => api.list('/invoices', params: any(named: 'params')))
          .thenAnswer((_) async => listResponse([_invoiceJson()]));

      final result = await repo.getInvoices();

      expect(result, isA<PaginatedList<Invoice>>());
      expect(result.items, hasLength(1));
      expect(result.items.first.status, 'pending');
    });

    test('returns cached invoices when available', () async {
      when(() => cache.get('invoices:first'))
          .thenAnswer((_) async => [_invoiceJson()]);

      final result = await repo.getInvoices();

      expect(result.items, hasLength(1));
      verifyNever(() => api.list(any(), params: any(named: 'params')));
    });

    test('passes cursor param when provided', () async {
      when(() => api.list('/invoices', params: any(named: 'params')))
          .thenAnswer((_) async => listResponse([]));

      await repo.getInvoices(cursor: 'cur-1');

      final params = verify(
        () => api.list('/invoices', params: captureAny(named: 'params')),
      ).captured.first as Map<String, dynamic>;
      expect(params['cursor'], 'cur-1');
    });

    test('propagates API error', () async {
      when(() => api.list(any(), params: any(named: 'params')))
          .thenThrow(offlineError());
      expect(() => repo.getInvoices(), throwsA(isA<ApiClientError>()));
    });
  });

  group('getInvoiceDetail', () {
    test('fetches invoice detail by id', () async {
      when(() => api.get('/invoices/inv-1'))
          .thenAnswer((_) async => response(_invoiceJson()));
      final result = await repo.getInvoiceDetail('inv-1');
      expect(result.id, 'inv-1');
      expect(result.totalAmount, 3500.0);
    });
  });

  group('createPayment', () {
    test('posts payment and invalidates invoice cache', () async {
      when(() => api.post('/payments/initiate', body: any(named: 'body')))
          .thenAnswer((_) async => response(_paymentJson()));

      final result = await repo.createPayment(
        invoiceId: 'inv-1',
        amount: 3500.0,
        method: 'bank_transfer',
      );

      expect(result.amount, 3500.0);
      verify(() => cache.invalidatePrefix('invoices:')).called(1);
    });
  });

  group('getInvoicePayments', () {
    test('returns list of payments for an invoice', () async {
      when(() => api.list('/payments/inv-1'))
          .thenAnswer((_) async => listResponse([_paymentJson()]));

      final result = await repo.getInvoicePayments('inv-1');

      expect(result, hasLength(1));
      expect(result.first.method, 'bank_transfer');
    });
  });

  group('getSiblingPolicy', () {
    test('fetches sibling policy', () async {
      when(() => api.get('/billing/sibling-policy')).thenAnswer(
        (_) async => response({
          'max_siblings_covered': 3,
          'discounts': <dynamic>[],
        }),
      );

      final result = await repo.getSiblingPolicy();

      expect(result, isA<SiblingPolicy>());
      expect(result.maxSiblingsCovered, 3);
    });
  });
}
