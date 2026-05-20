/// Program repository implementation — offline-first with cache.
///
/// Reference: G49 Phase 3 — Mobile read-only screens for current program +
/// academic history.
///
/// Endpoints:
///   GET /students/:id/current-program
///   GET /students/:id/academic-timeline
///   GET /students/:id/program-history
///   GET /students/:id/snapshots
///   GET /students/:id/transcript/pdf
///   GET /academic-snapshots/:id/transcript/pdf
///
/// Caching: 10-minute TTL using `CacheTtl.results` (the same policy used
/// by the existing results repository — academic history changes
/// infrequently and tolerates a short stale window).

import 'dart:io';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/core/storage/cache_store.dart';
import 'package:ecole_platform/domain/entities/academic/program.dart';
import 'package:ecole_platform/domain/repositories/academic/program_repository.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

class ProgramRepositoryImpl implements ProgramRepository {
  final ApiClient _api;
  final CacheStore _cache;

  ProgramRepositoryImpl({required ApiClient api, required CacheStore cache})
      : _api = api,
        _cache = cache;

  @override
  Future<CurrentProgram> getCurrentProgram(String studentId) async {
    // Single-object endpoint — no caching, but the screen polls infrequently
    // (refresh on pull-to-refresh only).
    final resp = await _api.get('/students/$studentId/current-program');
    return currentProgramFromJson(resp.data);
  }

  @override
  Future<List<AcademicTimelineEntry>> getAcademicTimeline(
    String studentId,
  ) async {
    final cacheKey = 'program-timeline:$studentId';

    final cached = await _cache.get(cacheKey);
    if (cached != null) {
      return cached.map(academicTimelineEntryFromJson).toList();
    }

    final resp = await _api.list('/students/$studentId/academic-timeline');
    await _cache.put(cacheKey, resp.data, CacheTtl.results);
    return resp.data.map(academicTimelineEntryFromJson).toList();
  }

  @override
  Future<List<ProgramAssignmentEvent>> getProgramHistory(
    String studentId,
  ) async {
    final cacheKey = 'program-history:$studentId';

    final cached = await _cache.get(cacheKey);
    if (cached != null) {
      return cached.map(programAssignmentEventFromJson).toList();
    }

    final resp = await _api.list('/students/$studentId/program-history');
    await _cache.put(cacheKey, resp.data, CacheTtl.results);
    return resp.data.map(programAssignmentEventFromJson).toList();
  }

  @override
  Future<List<AcademicSnapshotSummary>> getStudentSnapshots(
    String studentId,
  ) async {
    final cacheKey = 'program-snapshots:$studentId';

    final cached = await _cache.get(cacheKey);
    if (cached != null) {
      return cached.map(academicSnapshotSummaryFromJson).toList();
    }

    final resp = await _api.list('/students/$studentId/snapshots');
    await _cache.put(cacheKey, resp.data, CacheTtl.results);
    return resp.data.map(academicSnapshotSummaryFromJson).toList();
  }

  @override
  Future<File> downloadTranscriptPdf({
    required String studentId,
    required String academicYearId,
    String mode = 'preview',
    String lang = 'fr',
  }) async {
    final directory = await getTemporaryDirectory();
    final savePath = p.join(
      directory.path,
      'transcript-$studentId-$academicYearId.pdf',
    );
    final query = Uri(
      path: '/students/$studentId/transcript/pdf',
      queryParameters: {
        'academic_year_id': academicYearId,
        'mode': mode,
        'lang': lang,
      },
    ).toString();
    return _api.download(query, savePath: savePath);
  }

  @override
  Future<File> downloadSnapshotTranscriptPdf({
    required String snapshotId,
    String lang = 'fr',
  }) async {
    final directory = await getTemporaryDirectory();
    final savePath =
        p.join(directory.path, 'transcript-snapshot-$snapshotId.pdf');
    final query = Uri(
      path: '/academic-snapshots/$snapshotId/transcript/pdf',
      queryParameters: {
        'lang': lang,
      },
    ).toString();
    return _api.download(query, savePath: savePath);
  }
}
