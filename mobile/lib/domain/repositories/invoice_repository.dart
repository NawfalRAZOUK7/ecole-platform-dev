/// Invoice repository interface — domain layer contract.
import '../entities/invoice.dart';
import 'feed_repository.dart'; // for PaginatedList

abstract class InvoiceRepository {
  /// Fetch invoices with cursor pagination.
  Future<PaginatedList<Invoice>> getInvoices({String? cursor});
}
