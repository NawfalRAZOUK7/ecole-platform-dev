class CalendarClassOption {
  final String id;
  final String label;

  const CalendarClassOption({
    required this.id,
    required this.label,
  });
}

class ReminderPreference {
  final String eventType;
  final bool enabled;

  const ReminderPreference({
    required this.eventType,
    required this.enabled,
  });
}

class CalendarOptions {
  final List<CalendarClassOption> classes;
  final String icalUrl;
  final List<ReminderPreference> reminderPreferences;

  const CalendarOptions({
    this.classes = const [],
    this.icalUrl = '',
    this.reminderPreferences = const [],
  });
}

class CalendarEvent {
  final String id;
  final String instanceId;
  final String source;
  final String titleFr;
  final String? titleAr;
  final String? titleEn;
  final String? description;
  final String type;
  final String visibility;
  final String startAt;
  final String endAt;
  final String? location;
  final double? latitude;
  final double? longitude;
  final String? classId;
  final List<String> roleCodes;
  final int? capacity;
  final String? rsvpDeadline;
  final int attendeeCount;
  final int maybeCount;
  final int declinedCount;
  final String? myRsvp;
  final bool isAllDay;
  final bool isRecurring;
  final Map<String, dynamic>? recurrenceRule;
  final bool canEdit;
  final bool canDelete;
  final bool canRsvp;
  final bool isHoliday;
  final List<EventRsvpRecord> rsvps;

  const CalendarEvent({
    required this.id,
    required this.instanceId,
    required this.source,
    required this.titleFr,
    this.titleAr,
    this.titleEn,
    this.description,
    required this.type,
    required this.visibility,
    required this.startAt,
    required this.endAt,
    this.location,
    this.latitude,
    this.longitude,
    this.classId,
    this.roleCodes = const [],
    this.capacity,
    this.rsvpDeadline,
    this.attendeeCount = 0,
    this.maybeCount = 0,
    this.declinedCount = 0,
    this.myRsvp,
    this.isAllDay = false,
    this.isRecurring = false,
    this.recurrenceRule,
    this.canEdit = false,
    this.canDelete = false,
    this.canRsvp = false,
    this.isHoliday = false,
    this.rsvps = const [],
  });

  CalendarEvent copyWith({
    String? myRsvp,
    int? attendeeCount,
    int? maybeCount,
    int? declinedCount,
    List<EventRsvpRecord>? rsvps,
  }) {
    return CalendarEvent(
      id: id,
      instanceId: instanceId,
      source: source,
      titleFr: titleFr,
      titleAr: titleAr,
      titleEn: titleEn,
      description: description,
      type: type,
      visibility: visibility,
      startAt: startAt,
      endAt: endAt,
      location: location,
      latitude: latitude,
      longitude: longitude,
      classId: classId,
      roleCodes: roleCodes,
      capacity: capacity,
      rsvpDeadline: rsvpDeadline,
      attendeeCount: attendeeCount ?? this.attendeeCount,
      maybeCount: maybeCount ?? this.maybeCount,
      declinedCount: declinedCount ?? this.declinedCount,
      myRsvp: myRsvp ?? this.myRsvp,
      isAllDay: isAllDay,
      isRecurring: isRecurring,
      recurrenceRule: recurrenceRule,
      canEdit: canEdit,
      canDelete: canDelete,
      canRsvp: canRsvp,
      isHoliday: isHoliday,
      rsvps: rsvps ?? this.rsvps,
    );
  }
}

class EventRsvpRecord {
  final String userId;
  final String fullName;
  final String role;
  final String status;
  final String respondedAt;

  const EventRsvpRecord({
    required this.userId,
    required this.fullName,
    required this.role,
    required this.status,
    required this.respondedAt,
  });
}
