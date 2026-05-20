/// Program repository interface — domain layer contract for academic
/// program management & student academic history (G49 Phase 3).
import 'dart:io';

import 'package:ecole_platform/domain/entities/academic/program.dart';

abstract class ProgramRepository {
  /// Latest active enrollment's program for a student.
  Future<CurrentProgram> getCurrentProgram(String studentId);

  /// Year-grouped enrollment timeline (oldest first) for a student.
  Future<List<AcademicTimelineEntry>> getAcademicTimeline(String studentId);

  /// Append-only program-change events for a student, newest first.
  Future<List<ProgramAssignmentEvent>> getProgramHistory(String studentId);

  /// Frozen academic snapshots for a student, newest first.
  Future<List<AcademicSnapshotSummary>> getStudentSnapshots(String studentId);

  /// Download the official transcript PDF for a student + academic year.
  Future<File> downloadTranscriptPdf({
    required String studentId,
    required String academicYearId,
    String mode = 'preview',
    String lang = 'fr',
  });

  /// Download transcript PDF rendered from a frozen academic snapshot.
  Future<File> downloadSnapshotTranscriptPdf({
    required String snapshotId,
    String lang = 'fr',
  });
}
