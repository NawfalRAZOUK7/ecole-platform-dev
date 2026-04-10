/// Invoice repository interface — domain layer contract.
import 'dart:io';

import '../entities/invoice.dart';
import 'feed_repository.dart'; // for PaginatedList

abstract class InvoiceRepository {
  /// Fetch invoices with cursor pagination.
  Future<PaginatedList<Invoice>> getInvoices({String? cursor});

  Future<Invoice> getInvoiceDetail(String id);

  Future<InvoicePaymentRecord> createPayment({
    required String invoiceId,
    required double amount,
    required String method,
  });

  Future<void> uploadPaymentProof({
    required String paymentId,
    required File file,
  });

  Future<List<InvoicePaymentRecord>> getInvoicePayments(String invoiceId);

  Future<File> downloadInvoicePdf(String invoiceId);
}
