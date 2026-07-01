import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/core/storage/events_store.dart';
import 'package:ecole_platform/domain/entities/communication/calendar_event.dart';
import 'package:ecole_platform/domain/repositories/communication/calendar_repository.dart';

class CalendarRepositoryImpl implements CalendarRepository {
  final ApiClient _api;
  final EventsStore _eventsStore;

  CalendarRepositoryImpl({
    required ApiClient api,
    required EventsStore eventsStore,
  })  : _api = api,
        _eventsStore = eventsStore;

  @override
  Future<CalendarOptions> getCalendarOptions() async {
    final response = await _api.get('/calendar/options');
    return CalendarOptions(
      classes: (response.data['classes'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>()
          .map(calendarClassOptionFromJson)
          .toList(),
      icalUrl: response.data['ical_url'] as String? ?? '',
      reminderPreferences:
          (response.data['reminder_preferences'] as List<dynamic>? ?? const [])
              .cast<Map<String, dynamic>>()
              .map(reminderPreferenceFromJson)
              .toList(),
    );
  }

  @override
  Future<List<CalendarEvent>> getEvents({
    required String fromDate,
    required String toDate,
    String? classId,
  }) async {
    final monthKey = fromDate.substring(0, 7);
    try {
      final response = await _api.list(
        '/events',
        params: {
          'from': fromDate,
          'to': toDate,
          if (classId != null && classId.isNotEmpty) 'class_id': classId,
        },
      );
      await _eventsStore.replaceMonth(monthKey, response.data);
      return response.data.map(calendarEventFromJson).toList();
    } on ApiClientError {
      final cached = await _eventsStore.readMonth(monthKey);
      return cached.map(calendarEventFromJson).toList();
    }
  }

  @override
  Future<CalendarEvent> getEvent(String eventId) async {
    final response = await _api.get('/events/$eventId');
    return calendarEventFromJson(response.data);
  }

  @override
  Future<CalendarEvent> createEvent(Map<String, dynamic> payload) async {
    final response = await _api.post('/events', body: payload);
    return calendarEventFromJson(response.data);
  }

  @override
  Future<CalendarEvent> updateEvent(
    String eventId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.put('/events/$eventId', body: payload);
    return calendarEventFromJson(response.data);
  }

  @override
  Future<void> deleteEvent(String eventId) async {
    await _api.delete('/events/$eventId');
  }

  @override
  Future<CalendarEvent> respondToEvent(String eventId, String status) async {
    await _api.post('/events/$eventId/rsvp', body: {'status': status});
    return getEvent(eventId);
  }

  @override
  Future<List<CalendarEvent>> getCachedMonthEvents(String monthKey) async {
    final cached = await _eventsStore.readMonth(monthKey);
    return cached.map(calendarEventFromJson).toList();
  }
}
