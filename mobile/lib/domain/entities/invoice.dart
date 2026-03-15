/// Invoice entity — billing invoice entry.
///
/// Maps to GET /invoices response (InvoiceResponse schema).
class Invoice {
  final String id;
  final String schoolId;
  final String parentId;
  final String? periodId;
  final String status;
  final double totalAmount;
  final String currency;
  final String issuedDate;
  final String dueDate;
  final List<InvoiceItem> items;

  const Invoice({
    required this.id,
    required this.schoolId,
    required this.parentId,
    this.periodId,
    required this.status,
    required this.totalAmount,
    required this.currency,
    required this.issuedDate,
    required this.dueDate,
    required this.items,
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
