import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/data/repositories_impl/invoice_repository_impl.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  test('lists invoices and writes the result to cache', () async {
    final api = MockApiClient();
    final cache = MockCacheStore();
    final repository = InvoiceRepositoryImpl(api: api, cache: cache);

    when(() => cache.get('invoices:first')).thenAnswer((_) async => null);
    when(() => api.list('/invoices', params: <String, dynamic>{})).thenAnswer(
      (_) async => listResponse(
        const [
          {
            'id': 'invoice-1',
            'school_id': 'school-1',
            'parent_id': 'parent-1',
            'status': 'pending',
            'total_amount': 1200,
            'currency': 'MAD',
            'issued_date': '2026-04-01',
            'due_date': '2026-04-15',
            'items': [
              {
                'id': 'line-1',
                'description': 'Tuition',
                'amount': 1200,
                'unit_price': 1200,
                'quantity': 1,
              },
            ],
          },
        ],
      ),
    );
    when(
      () => cache.put('invoices:first', any(), any()),
    ).thenAnswer((_) async {});

    final invoices = await repository.getInvoices();

    expect(invoices.items.single.currency, 'MAD');
    verify(() => cache.put('invoices:first', any(), any())).called(1);
  });

  test('loads invoice detail', () async {
    final api = MockApiClient();
    final repository = InvoiceRepositoryImpl(
      api: api,
      cache: MockCacheStore(),
    );

    when(() => api.get('/invoices/invoice-1')).thenAnswer(
      (_) async => response(
        const {
          'id': 'invoice-1',
          'school_id': 'school-1',
          'parent_id': 'parent-1',
          'status': 'pending',
          'total_amount': 1200,
          'currency': 'MAD',
          'issued_date': '2026-04-01',
          'due_date': '2026-04-15',
          'items': [
            {
              'id': 'line-1',
              'description': 'Tuition',
              'amount': 1200,
              'unit_price': 1200,
              'quantity': 1,
            },
          ],
        },
      ),
    );

    final invoice = await repository.getInvoiceDetail('invoice-1');

    expect(invoice.id, 'invoice-1');
    expect(invoice.items.single.description, 'Tuition');
  });

  test('uploads payment proof through the API client', () async {
    final api = MockApiClient();
    final repository = InvoiceRepositoryImpl(
      api: api,
      cache: MockCacheStore(),
    );
    final file = File(
      '${Directory.systemTemp.path}/invoice-payment-proof-test.txt',
    )..writeAsStringSync('proof');

    when(
      () => api.uploadFile('/payments/payment-1/proof', file: file),
    ).thenAnswer((_) async => response(const {'ok': true}));

    await repository.uploadPaymentProof(paymentId: 'payment-1', file: file);

    verify(() => api.uploadFile('/payments/payment-1/proof', file: file))
        .called(1);
    await file.delete();
  });
}
