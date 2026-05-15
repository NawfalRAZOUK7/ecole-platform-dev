/// Invoice entity — billing invoice entry.
///
/// Maps to GET /invoices response (InvoiceResponse schema).
class Invoice {
  final String id;
  final String schoolId;
  final String parentId;
  final String? periodId;
  final String? invoiceNumber;
  final String? studentId;
  final String? studentName;
  final String? label;
  final String status;
  final double totalAmount;
  final String currency;
  final String issuedDate;
  final String dueDate;
  final List<InvoiceItem> items;
  final double? balanceDue;

  const Invoice({
    required this.id,
    required this.schoolId,
    required this.parentId,
    this.periodId,
    this.invoiceNumber,
    this.studentId,
    this.studentName,
    this.label,
    required this.status,
    required this.totalAmount,
    required this.currency,
    required this.issuedDate,
    required this.dueDate,
    required this.items,
    this.balanceDue,
  });
}

class InvoiceItem {
  final String id;
  final String description;
  final double amount;
  final double unitPrice;
  final int quantity;

  const InvoiceItem({
    required this.id,
    required this.description,
    required this.amount,
    required this.unitPrice,
    required this.quantity,
  });
}

class InvoicePaymentRecord {
  final String id;
  final String invoiceId;
  final double amount;
  final String method;
  final String status;
  final String? createdAt;
  final String? finalizedAt;
  final String? proofUrl;

  const InvoicePaymentRecord({
    required this.id,
    required this.invoiceId,
    required this.amount,
    required this.method,
    required this.status,
    this.createdAt,
    this.finalizedAt,
    this.proofUrl,
  });
}

class SiblingDiscountTier {
  final int siblingRank;
  final double discountPercent;

  const SiblingDiscountTier({
    required this.siblingRank,
    required this.discountPercent,
  });
}

class SiblingPolicy {
  final String? id;
  final List<SiblingDiscountTier> discounts;
  final int maxSiblingsCovered;

  const SiblingPolicy({
    this.id,
    required this.discounts,
    required this.maxSiblingsCovered,
  });
}

class LateFeePolicy {
  final String? id;
  final int gracePeriodDays;
  final double feePercent;
  final double maxFeeCap;

  const LateFeePolicy({
    this.id,
    required this.gracePeriodDays,
    required this.feePercent,
    required this.maxFeeCap,
  });
}

class PaymentPlanDraftInstallment {
  final String dueDate;
  final double amount;

  const PaymentPlanDraftInstallment({
    required this.dueDate,
    required this.amount,
  });
}

class PaymentPlanInstallment {
  final String id;
  final String planId;
  final String dueDate;
  final double amount;
  final String status;
  final String? paidAt;

  const PaymentPlanInstallment({
    required this.id,
    required this.planId,
    required this.dueDate,
    required this.amount,
    required this.status,
    this.paidAt,
  });
}

class PaymentPlan {
  final String id;
  final String studentId;
  final String? studentName;
  final String name;
  final double totalAmount;
  final String startDate;
  final String status;
  final List<PaymentPlanInstallment> installments;
  final String createdAt;

  const PaymentPlan({
    required this.id,
    required this.studentId,
    this.studentName,
    required this.name,
    required this.totalAmount,
    required this.startDate,
    required this.status,
    required this.installments,
    required this.createdAt,
  });
}
