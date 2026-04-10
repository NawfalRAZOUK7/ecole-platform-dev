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
