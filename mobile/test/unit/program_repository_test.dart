/// Unit tests for ProgramRepositoryImpl + DTO mappers (G49 Phase 3).
///
/// Mirrors the patterns in repositories_test.dart and entities_test.dart.

import 'dart:io';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/data/repositories_impl/program_repository_impl.dart';
import 'package:ecole_platform/domain/entities/program.dart';

import '../helpers/test_mocks.dart';

ApiResponse<Map<String, dynamic>> _response(Map<String, dynamic> data) {
  return ApiResponse<Map<String, dynamic>>(data: data);
}

ApiListResponse<Map<String, dynamic>> _listResponse(
  List<Map<String, dynamic>> data, {
  String? nextCursor,
  bool hasMore = false,
}) {
  return ApiListResponse<Map<String, dynamic>>(
    data: data,
    nextCursor: nextCursor,
    hasMore: hasMore,
  );
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const pathProviderChannel = MethodChannel('plugins.flutter.io/path_provider');

  setUpAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(pathProviderChannel, (call) async {
      if (call.method == 'getTemporaryDirectory') {
        return '/tmp';
      }
      return null;
    });
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(pathProviderChannel, null);
  });

  group('Program DTO mappers', () {
    test('programSummaryFromJson handles required fields', () {
      final summary = programSummaryFromJson({
        'id': 'prog-1',
        'code': 'SCI-MATH',
        'name': 'Sciences Mathématiques',
        'version_label': '1.0',
      });
      expect(summary, isNotNull);
      expect(summary!.id, 'prog-1');
      expect(summary.code, 'SCI-MATH');
      expect(summary.versionLabel, '1.0');
    });

    test('programSummaryFromJson returns null for null input', () {
      expect(programSummaryFromJson(null), isNull);
    });

    test('currentProgramFromJson maps a populated payload', () {
      final current = currentProgramFromJson({
        'student_id': 'std-1',
        'academic_year_id': 'ay-1',
        'period_id': 'p-1',
        'enrollment_id': 'enr-1',
        'program': {
          'id': 'prog-1',
          'code': 'SCI-MATH',
          'name': 'Sciences Mathématiques',
          'version_label': '1.0',
        },
      });
      expect(current.studentId, 'std-1');
      expect(current.program?.code, 'SCI-MATH');
    });

    test('currentProgramFromJson maps the empty/no-active shape', () {
      final current = currentProgramFromJson({
        'student_id': 'std-1',
        'academic_year_id': null,
        'period_id': null,
        'enrollment_id': null,
        'program': null,
      });
      expect(current.program, isNull);
      expect(current.enrollmentId, isNull);
    });

    test('academicTimelineEntryFromJson maps a row with a program', () {
      final entry = academicTimelineEntryFromJson({
        'enrollment_id': 'enr-1',
        'academic_year_id': 'ay-1',
        'academic_year_label': '2026-2027',
        'academic_year_start': '2026-09-01',
        'academic_year_end': '2027-07-15',
        'period_id': 'p-1',
        'period_label': 'Trimester 1',
        'period_start': '2026-09-01',
        'period_end': '2026-12-20',
        'class_id': 'cls-1',
        'class_code': '3A',
        'class_name': 'Classe 3A',
        'program': {
          'id': 'prog-1',
          'code': 'TC',
          'name': 'Tronc Commun',
          'version_label': '1.0',
        },
        'status': 'active',
      });
      expect(entry.classCode, '3A');
      expect(entry.program?.code, 'TC');
      expect(entry.status, 'active');
    });

    test('programAssignmentEventFromJson maps a TRANSFER event', () {
      final event = programAssignmentEventFromJson({
        'id': 'evt-1',
        'school_id': 'school-1',
        'student_id': 'std-1',
        'academic_year_id': 'ay-1',
        'period_id': 'p-1',
        'from_program_id': 'prog-1',
        'to_program_id': 'prog-2',
        'from_enrollment_id': 'enr-1',
        'to_enrollment_id': 'enr-2',
        'reason_code': 'TRANSFER',
        'reason_note': 'parent request',
        'actor_user_id': 'user-1',
        'occurred_at': '2026-10-01T00:00:00Z',
      });
      expect(event.reasonCode, ProgramAssignmentReason.transfer);
      expect(event.reasonCodeWire, 'TRANSFER');
      expect(event.reasonNote, 'parent request');
      expect(event.fromProgramId, 'prog-1');
      expect(event.toProgramId, 'prog-2');
    });

    test('ProgramAssignmentReason.fromWire handles unknown values gracefully',
        () {
      expect(
        ProgramAssignmentReason.fromWire('NOT-A-REAL-CODE'),
        ProgramAssignmentReason.initial,
      );
    });
  });

  group('ProgramRepositoryImpl', () {
    setUpAll(registerTestFallbacks);

    test('getCurrentProgram bypasses the cache and hits the API', () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = ProgramRepositoryImpl(api: api, cache: cache);

      when(() => api.get('/students/std-1/current-program')).thenAnswer(
        (_) async => _response({
          'student_id': 'std-1',
          'academic_year_id': 'ay-1',
          'period_id': 'p-1',
          'enrollment_id': 'enr-1',
          'program': {
            'id': 'prog-1',
            'code': 'SCI-MATH',
            'name': 'Sciences Mathématiques',
            'version_label': '1.0',
          },
        }),
      );

      final result = await repository.getCurrentProgram('std-1');
      expect(result.program?.code, 'SCI-MATH');
      verifyNever(() => cache.get(any()));
      verifyNever(() => cache.put(any(), any(), any()));
    });

    test('getAcademicTimeline returns the cached payload on hit', () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = ProgramRepositoryImpl(api: api, cache: cache);

      when(() => cache.get('program-timeline:std-1')).thenAnswer(
        (_) async => [
          {
            'enrollment_id': 'enr-1',
            'academic_year_id': 'ay-1',
            'academic_year_label': '2026-2027',
            'academic_year_start': '2026-09-01',
            'academic_year_end': '2027-07-15',
            'period_id': 'p-1',
            'period_label': 'Trimester 1',
            'period_start': '2026-09-01',
            'period_end': '2026-12-20',
            'class_id': 'cls-1',
            'class_code': '3A',
            'class_name': 'Classe 3A',
            'program': null,
            'status': 'active',
          },
        ],
      );

      final result = await repository.getAcademicTimeline('std-1');
      expect(result, hasLength(1));
      expect(result.single.classCode, '3A');
      verifyNever(() => api.list(any(), params: any(named: 'params')));
    });

    test('getProgramHistory hits the API on cache miss and stores the payload',
        () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = ProgramRepositoryImpl(api: api, cache: cache);

      when(() => cache.get('program-history:std-1'))
          .thenAnswer((_) async => null);
      when(() => api.list('/students/std-1/program-history')).thenAnswer(
        (_) async => _listResponse(const [
          {
            'id': 'evt-1',
            'school_id': 'school-1',
            'student_id': 'std-1',
            'academic_year_id': 'ay-1',
            'period_id': 'p-1',
            'from_program_id': null,
            'to_program_id': 'prog-1',
            'from_enrollment_id': 'enr-1',
            'to_enrollment_id': 'enr-1',
            'reason_code': 'INITIAL',
            'reason_note': null,
            'actor_user_id': 'user-1',
            'occurred_at': '2026-09-01T00:00:00Z',
          }
        ]),
      );
      when(() => cache.put('program-history:std-1', any(), any()))
          .thenAnswer((_) async {});

      final result = await repository.getProgramHistory('std-1');
      expect(result, hasLength(1));
      expect(result.single.reasonCode, ProgramAssignmentReason.initial);
      verify(() => cache.put('program-history:std-1', any(), any())).called(1);
    });

    test('downloadTranscriptPdf hits the existing student transcript endpoint',
        () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = ProgramRepositoryImpl(api: api, cache: cache);
      final file = File('/tmp/transcript.pdf');

      when(
        () => api.download(
          any(),
          savePath: any(named: 'savePath'),
        ),
      ).thenAnswer((_) async => file);

      final result = await repository.downloadTranscriptPdf(
        studentId: 'std-1',
        academicYearId: 'ay-1',
        lang: 'en',
      );

      expect(result.path, '/tmp/transcript.pdf');
      verify(
        () => api.download(
          '/students/std-1/transcript/pdf?academic_year_id=ay-1&mode=preview&lang=en',
          savePath: any(named: 'savePath'),
        ),
      ).called(1);
    });

    test('getStudentSnapshots returns the cached payload on hit', () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = ProgramRepositoryImpl(api: api, cache: cache);

      when(() => cache.get('program-snapshots:std-1')).thenAnswer(
        (_) async => [
          {
            'id': 'snap-1',
            'school_id': 'school-1',
            'student_id': 'std-1',
            'academic_year_id': 'ay-1',
            'snapshot_kind': 'YEAR_END',
            'taken_at': '2026-07-01T10:00:00Z',
            'taken_by': 'user-1',
          },
        ],
      );

      final result = await repository.getStudentSnapshots('std-1');
      expect(result, hasLength(1));
      expect(result.single.snapshotKind, 'YEAR_END');
      verifyNever(() => api.list(any(), params: any(named: 'params')));
    });

    test(
        'downloadSnapshotTranscriptPdf hits the existing snapshot transcript endpoint',
        () async {
      final api = MockApiClient();
      final cache = MockCacheStore();
      final repository = ProgramRepositoryImpl(api: api, cache: cache);
      final file = File('/tmp/transcript-snapshot.pdf');

      when(
        () => api.download(
          any(),
          savePath: any(named: 'savePath'),
        ),
      ).thenAnswer((_) async => file);

      final result = await repository.downloadSnapshotTranscriptPdf(
        snapshotId: 'snap-1',
        lang: 'ar',
      );

      expect(result.path, '/tmp/transcript-snapshot.pdf');
      verify(
        () => api.download(
          '/academic-snapshots/snap-1/transcript/pdf?lang=ar',
          savePath: any(named: 'savePath'),
        ),
      ).called(1);
    });
  });
}
