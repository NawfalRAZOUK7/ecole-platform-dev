/// Result repository implementation — offline-first with cache.
///
/// Reference: S-099, DEC-E2-020 — Results 10min TTL

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/core/storage/cache_store.dart';
import 'package:ecole_platform/domain/entities/academic/result.dart';
import 'package:ecole_platform/domain/common/pagination.dart';
import 'package:ecole_platform/domain/repositories/academic/result_repository.dart';

class ResultRepositoryImpl implements ResultRepository {
  final ApiClient _api;
  final CacheStore _cache;

  ResultRepositoryImpl({required ApiClient api, required CacheStore cache})
      : _api = api,
        _cache = cache;

  @override
  Future<PaginatedList<Result>> getResults({String? cursor}) async {
    final cacheKey = 'results:${cursor ?? 'first'}';

    final cached = await _cache.get(cacheKey);
    if (cached != null) {
      return PaginatedList(
        items: cached.map(resultFromJson).toList(),
        hasMore: false,
      );
    }

    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;

    final resp = await _api.list('/results', params: params);
    await _cache.put(cacheKey, resp.data, CacheTtl.results);

    return PaginatedList(
      items: resp.data.map(resultFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }
}
