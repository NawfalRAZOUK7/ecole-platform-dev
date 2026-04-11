/// Timetable entities — slot, exception, weekly schedule.
///
/// Maps to GET /timetable/me/weekly and /timetable/class/{id}/weekly responses.

class TimetableSlot {
  final String id;
  final int dayOfWeek;
  final String startTime;
  final String endTime;
  final String subject;
  final String teacherId;
  final String? room;
  final bool isRecurring;
  final String classId;
  final String? className;
  final TimetableException? exception;

  const TimetableSlot({
    required this.id,
    required this.dayOfWeek,
    required this.startTime,
    required this.endTime,
    required this.subject,
    required this.teacherId,
    this.room,
    required this.isRecurring,
    required this.classId,
    this.className,
    this.exception,
  });

  factory TimetableSlot.fromJson(Map<String, dynamic> json) {
    return TimetableSlot(
      id: json['id'] as String,
      dayOfWeek: json['day_of_week'] as int,
      startTime: json['start_time'] as String,
      endTime: json['end_time'] as String,
      subject: json['subject'] as String,
      teacherId: json['teacher_id'] as String,
      room: json['room'] as String?,
      isRecurring: json['is_recurring'] as bool? ?? true,
      classId: json['class_id'] as String,
      className: json['class_name'] as String?,
      exception: json['exception'] != null
          ? TimetableException.fromJson(
              json['exception'] as Map<String, dynamic>)
          : null,
    );
  }
}

class TimetableException {
  final String exceptionType;
  final String? substituteTeacherId;
  final String? newRoom;
  final String? reason;

  const TimetableException({
    required this.exceptionType,
    this.substituteTeacherId,
    this.newRoom,
    this.reason,
  });

  factory TimetableException.fromJson(Map<String, dynamic> json) {
    return TimetableException(
      exceptionType: json['exception_type'] as String,
      substituteTeacherId: json['substitute_teacher_id'] as String?,
      newRoom: json['new_room'] as String?,
      reason: json['reason'] as String?,
    );
  }
}

class WeeklySchedule {
  final String academicYearId;
  final String weekStart;
  final String weekEnd;
  final List<TimetableSlot> slots;

  const WeeklySchedule({
    required this.academicYearId,
    required this.weekStart,
    required this.weekEnd,
    required this.slots,
  });

  factory WeeklySchedule.fromJson(Map<String, dynamic> json) {
    return WeeklySchedule(
      academicYearId: json['academic_year_id'] as String? ?? '',
      weekStart: json['week_start'] as String,
      weekEnd: json['week_end'] as String,
      slots: (json['slots'] as List<dynamic>)
          .map((s) => TimetableSlot.fromJson(s as Map<String, dynamic>))
          .toList(),
    );
  }
}

class TeacherAvailability {
  final String teacherId;
  final int dayOfWeek;
  final String availableFrom;
  final String availableUntil;

  const TeacherAvailability({
    required this.teacherId,
    required this.dayOfWeek,
    required this.availableFrom,
    required this.availableUntil,
  });

  factory TeacherAvailability.fromJson(Map<String, dynamic> json) {
    return TeacherAvailability(
      teacherId: json['teacher_id'] as String? ?? '',
      dayOfWeek: json['day_of_week'] as int? ?? 1,
      availableFrom: json['available_from'] as String? ?? '08:00',
      availableUntil: json['available_until'] as String? ?? '17:00',
    );
  }
}

class RoomConstraint {
  final String roomName;
  final int capacity;

  const RoomConstraint({
    required this.roomName,
    required this.capacity,
  });

  factory RoomConstraint.fromJson(Map<String, dynamic> json) {
    return RoomConstraint(
      roomName: json['room_name'] as String? ?? '',
      capacity: json['capacity'] as int? ?? 0,
    );
  }
}

class TimetableConstraints {
  final String academicYearId;
  final int maxConsecutiveClasses;
  final List<TeacherAvailability> teacherAvailability;
  final List<RoomConstraint> roomConstraints;

  const TimetableConstraints({
    required this.academicYearId,
    required this.maxConsecutiveClasses,
    required this.teacherAvailability,
    required this.roomConstraints,
  });

  factory TimetableConstraints.fromJson(Map<String, dynamic> json) {
    return TimetableConstraints(
      academicYearId: json['academic_year_id'] as String? ?? '',
      maxConsecutiveClasses: json['max_consecutive_classes'] as int? ?? 0,
      teacherAvailability:
          (json['teacher_availability'] as List<dynamic>? ?? const [])
              .cast<Map<String, dynamic>>()
              .map(TeacherAvailability.fromJson)
              .toList(),
      roomConstraints: (json['room_constraints'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>()
          .map(RoomConstraint.fromJson)
          .toList(),
    );
  }
}

class GenerationJob {
  final String jobId;
  final String status;
  final int progress;
  final String? error;
  final String createdAt;

  const GenerationJob({
    required this.jobId,
    required this.status,
    required this.progress,
    this.error,
    required this.createdAt,
  });

  factory GenerationJob.fromJson(Map<String, dynamic> json) {
    return GenerationJob(
      jobId: json['job_id'] as String? ?? '',
      status: json['status'] as String? ?? 'pending',
      progress: json['progress'] as int? ?? 0,
      error: json['error'] as String?,
      createdAt: json['created_at'] as String? ?? '',
    );
  }
}

class GeneratedSlot {
  final int dayOfWeek;
  final String startTime;
  final String endTime;
  final String subject;
  final String teacherId;
  final String? room;
  final String classId;

  const GeneratedSlot({
    required this.dayOfWeek,
    required this.startTime,
    required this.endTime,
    required this.subject,
    required this.teacherId,
    this.room,
    required this.classId,
  });

  factory GeneratedSlot.fromJson(Map<String, dynamic> json) {
    return GeneratedSlot(
      dayOfWeek: json['day_of_week'] as int? ?? 1,
      startTime: json['start_time'] as String? ?? '',
      endTime: json['end_time'] as String? ?? '',
      subject: json['subject'] as String? ?? '',
      teacherId: json['teacher_id'] as String? ?? '',
      room: json['room'] as String?,
      classId: json['class_id'] as String? ?? '',
    );
  }
}

class GenerationPreview {
  final String jobId;
  final List<GeneratedSlot> slots;
  final List<String> warnings;

  const GenerationPreview({
    required this.jobId,
    required this.slots,
    required this.warnings,
  });

  factory GenerationPreview.fromJson(Map<String, dynamic> json) {
    return GenerationPreview(
      jobId: json['job_id'] as String? ?? '',
      slots: (json['slots'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>()
          .map(GeneratedSlot.fromJson)
          .toList(),
      warnings: (json['warnings'] as List<dynamic>? ?? const [])
          .map((item) => item.toString())
          .toList(),
    );
  }
}

class ApplyGenerationResult {
  final int applied;
  final int skipped;

  const ApplyGenerationResult({
    required this.applied,
    required this.skipped,
  });

  factory ApplyGenerationResult.fromJson(Map<String, dynamic> json) {
    return ApplyGenerationResult(
      applied: json['applied'] as int? ?? 0,
      skipped: json['skipped'] as int? ?? 0,
    );
  }
}
