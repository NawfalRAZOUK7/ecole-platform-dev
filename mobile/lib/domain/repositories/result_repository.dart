/// Result repository interface — domain layer contract.
import '../entities/result.dart';
import 'feed_repository.dart'; // for PaginatedList

abstract class ResultRepository {
  /// Fetch results with cursor pagination.
  Future<PaginatedList<Result>> getResults({String? cursor});
}
