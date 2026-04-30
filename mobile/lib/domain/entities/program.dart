/// Program / academic-history entities — Phase 3 (G49).
///
/// Mirrors backend schemas in `app/schemas/programs.py`.
/// Kept dependency-free (no cache/API imports) so unit tests can construct
/// instances without bringing up the Dio stack.
library;

class ProgramSummary {
  final String id;
  final String code;
  final String name;
  final String versionLabel;

  const ProgramSummary({
    required this.id,
    required this.code,
    required this.name,
    required this.versionLabel,
  });
}

class Program {
  final String id;
  final String schoolId;
  final String code;
  final String name;
  final String? level;
  final String? description;
  final bool isActive;
  final String versionLabel;
  final String? effectiveFrom;
  final String createdAt;
  final String? updatedAt;

  const Program({
    required this.id,
    required this.schoolId,
    required this.code,
    required this.name,
    required this.isActive,
    required this.versionLabel,
    required this.createdAt,
    this.level,
    this.description,
    this.effectiveFrom,
    this.updatedAt,
  });
}

/// Reason for a ProgramAssignmentEvent. Mirrors the backend's
/// ProgramAssignmentReason enum and its `ck_prog_assignment_events_reason_code`
/// CHECK constraint.
enum ProgramAssignmentReason {
  initial('INITIAL'),
  transfer('TRANSFER'),
  promotion('PROMOTION'),
  correction('CORRECTION'),
  readmission('READMISSION');

  final String wireValue;
  const ProgramAssignmentReason(this.wireValue);

  /// Parse from the server-side wire value. Falls back to [initial] for
  /// forward-compatibility with future codes — the UI just shows a
  /// generic label for unknowns.
  static ProgramAssignmentReason fromWire(String value) {
    for (final reason in ProgramAssignmentReason.values) {
      if (reason.wireValue == value) {
        return reason;
      }
    }
    return ProgramAssignmentReason.initial;
  }
}

class ProgramAssignmentEvent {
  final String id;
  final String schoolId;
  final String studentId;
  final String academicYearId;
  final String? periodId;
  final String? fromProgramId;
  final String toProgramId;
  final String? fromEnrollmentId;
  final String? toEnrollmentId;
  final ProgramAssignmentReason reasonCode;
  final String reasonCodeWire;
  final String? reasonNote;
  final String? actorUserId;
  final String occurredAt;

  const ProgramAssignmentEvent({
    required this.id,
    required this.schoolId,
    required this.studentId,
    required this.academicYearId,
    required this.toProgramId,
    required this.reasonCode,
    required this.reasonCodeWire,
    required this.occurredAt,
    this.periodId,
    this.fromProgramId,
    this.fromEnrollmentId,
    this.toEnrollmentId,
    this.reasonNote,
    this.actorUserId,
  });
}

class AcademicTimelineEntry {
  final String enrollmentId;
  final String academicYearId;
  final String? academicYearLabel;
  final String academicYearStart;
  final String academicYearEnd;
  final String periodId;
  final String? periodLabel;
  final String periodStart;
  final String periodEnd;
  final String classId;
  final String classCode;
  final String className;
  final ProgramSummary? program;
  final String status;

  const AcademicTimelineEntry({
    required this.enrollmentId,
    required this.academicYearId,
    required this.academicYearStart,
    required this.academicYearEnd,
    required this.periodId,
    required this.periodStart,
    required this.periodEnd,
    required this.classId,
    required this.classCode,
    required this.className,
    required this.status,
    this.academicYearLabel,
    this.periodLabel,
    this.program,
  });
}

class CurrentProgram {
  final String studentId;
  final String? academicYearId;
  final String? periodId;
  final String? enrollmentId;
  final ProgramSummary? program;

  const CurrentProgram({
    required this.studentId,
    this.academicYearId,
    this.periodId,
    this.enrollmentId,
    this.program,
  });
}

class AcademicSnapshotSummary {
  final String id;
  final String schoolId;
  final String studentId;
  final String academicYearId;
  final String snapshotKind;
  final String takenAt;
  final String? takenBy;

  const AcademicSnapshotSummary({
    required this.id,
    required this.schoolId,
    required this.studentId,
    required this.academicYearId,
    required this.snapshotKind,
    required this.takenAt,
    this.takenBy,
  });
}
