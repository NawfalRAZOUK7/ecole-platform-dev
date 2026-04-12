import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/invoice.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/features/invoices/invoice_detail_screen.dart';
import 'package:ecole_platform/features/invoices/invoices_screen.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  testWidgets('InvoicesScreen renders invoice list', (tester) async {
    final repository = MockInvoiceRepository();
    when(() => repository.getInvoices()).thenAnswer(
      (_) async =>
          PaginatedList<Invoice>(items: [createInvoice()], hasMore: false),
    );

    await pumpApp(
      tester,
      const InvoicesScreen(),
      overrides: buildMockRepositoryOverrides(invoiceRepository: repository),
    );
    await tester.pumpAndSettle();

    expect(find.text('Monthly tuition'), findsOneWidget);
    expect(find.textContaining('MAD'), findsWidgets);
  });

  testWidgets('InvoiceDetailScreen renders amounts in MAD', (tester) async {
    final repository = MockInvoiceRepository();

    when(() => repository.getInvoiceDetail('invoice-1')).thenAnswer(
      (_) async => createInvoice(),
    );
    when(() => repository.getInvoicePayments('invoice-1')).thenAnswer(
      (_) async => const [],
    );

    await pumpApp(
      tester,
      const InvoiceDetailScreen(invoiceId: 'invoice-1'),
      overrides: buildMockRepositoryOverrides(invoiceRepository: repository),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('MAD'), findsWidgets);
    expect(find.text('Monthly tuition'), findsOneWidget);
  });

  testWidgets('InvoiceDetailScreen shows payment proof upload action',
      (tester) async {
    final repository = MockInvoiceRepository();

    when(() => repository.getInvoiceDetail('invoice-1')).thenAnswer(
      (_) async => createInvoice(),
    );
    when(() => repository.getInvoicePayments('invoice-1')).thenAnswer(
      (_) async => const [
        InvoicePaymentRecord(
          id: 'payment-1',
          invoiceId: 'invoice-1',
          amount: 1200,
          method: 'card',
          status: 'pending',
        ),
      ],
    );

    await pumpApp(
      tester,
      const InvoiceDetailScreen(invoiceId: 'invoice-1'),
      overrides: buildMockRepositoryOverrides(invoiceRepository: repository),
    );
    await tester.pumpAndSettle();

    expect(find.text('Upload proof'), findsOneWidget);
  });
}
