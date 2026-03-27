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
          ? TimetableException.fromJson(json['exception'] as Map<String, dynamic>)
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
