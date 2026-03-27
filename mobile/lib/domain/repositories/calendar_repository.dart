import 'package:ecole_platform/domain/entities/calendar_event.dart';

abstract class CalendarRepository {
  Future<CalendarOptions> getCalendarOptions();

  Future<List<CalendarEvent>> getEvents({
    required String fromDate,
    required String toDate,
    String? classId,
  });

  Future<CalendarEvent> getEvent(String eventId);

  Future<CalendarEvent> createEvent(Map<String, dynamic> payload);

  Future<CalendarEvent> updateEvent(
      String eventId, Map<String, dynamic> payload);

  Future<void> deleteEvent(String eventId);

  Future<CalendarEvent> respondToEvent(String eventId, String status);

  Future<List<CalendarEvent>> getCachedMonthEvents(String monthKey);
}
