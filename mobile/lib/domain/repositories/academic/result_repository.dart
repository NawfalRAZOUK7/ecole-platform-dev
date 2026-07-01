/// Result repository interface — domain layer contract.
import 'package:ecole_platform/domain/entities/academic/result.dart';
import 'package:ecole_platform/domain/common/pagination.dart';

abstract class ResultRepository {
  /// Fetch results with cursor pagination.
  Future<PaginatedList<Result>> getResults({String? cursor});
}
