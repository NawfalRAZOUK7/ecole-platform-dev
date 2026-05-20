/// Invoice repository interface — domain layer contract.
import 'dart:io';

import 'package:ecole_platform/domain/entities/billing/invoice.dart';
import 'package:ecole_platform/domain/common/pagination.dart';

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

  Future<File> downloadInvoicePdf(String invoiceId, {String language = 'fr'});

  Future<File> downloadPaymentReceipt(
    String paymentId, {
    String language = 'fr',
  });

  Future<SiblingPolicy> getSiblingPolicy();

  Future<SiblingPolicy> updateSiblingPolicy({
    required List<SiblingDiscountTier> discounts,
    required int maxSiblingsCovered,
  });

  Future<LateFeePolicy> getLateFeePolicy();

  Future<LateFeePolicy> updateLateFeePolicy({
    required int gracePeriodDays,
    required double feePercent,
    required double maxFeeCap,
  });

  Future<List<PaymentPlan>> listPaymentPlans({String? status});

  Future<PaymentPlan> getPaymentPlan(String id);

  Future<PaymentPlan> createPaymentPlan({
    required String studentId,
    required String name,
    required double totalAmount,
    required String startDate,
    required List<PaymentPlanDraftInstallment> installments,
  });
}
