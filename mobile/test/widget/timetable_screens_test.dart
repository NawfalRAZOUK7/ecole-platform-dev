import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/features/academic/timetable/timetable_screen.dart';

import '../helpers/api_responses.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  testWidgets('TimetableScreen renders the timetable grid on tablet width',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(900, 700));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final api = MockApiClient();
    when(() => api.get('/timetable/me/weekly')).thenAnswer(
      (_) async => response(_scheduleJson(slots: [_slotJson(day: 1)])),
    );

    await pumpApp(
      tester,
      const TimetableScreen(),
      overrides: [apiClientProvider.overrideWithValue(api)],
      wrapWithScaffold: false,
    );
    await _settle(tester);

    expect(find.text('Mathematics'), findsOneWidget);
    expect(find.byType(Card), findsWidgets);
  });

  testWidgets('TimetableScreen renders the weekly page view on phone width',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(390, 844));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final api = MockApiClient();
    when(() => api.get('/timetable/me/weekly')).thenAnswer(
      (_) async => response(
        _scheduleJson(
          slots: [
            _slotJson(day: 1),
            _slotJson(day: 2, subject: 'Physics'),
          ],
        ),
      ),
    );

    await pumpApp(
      tester,
      const TimetableScreen(),
      overrides: [apiClientProvider.overrideWithValue(api)],
      wrapWithScaffold: false,
    );
    await _settle(tester);

    expect(find.text('Mathematics'), findsOneWidget);
  });

  testWidgets('TimetableScreen shows the empty state when there are no slots',
      (tester) async {
    final api = MockApiClient();
    when(() => api.get('/timetable/me/weekly')).thenAnswer(
      (_) async => response(_scheduleJson(slots: const [])),
    );

    await pumpApp(
      tester,
      const TimetableScreen(),
      overrides: [apiClientProvider.overrideWithValue(api)],
      wrapWithScaffold: false,
    );
    await _settle(tester);

    expect(find.byIcon(Icons.calendar_today), findsOneWidget);
    expect(find.byType(Card), findsNothing);
  });
}

Map<String, dynamic> _scheduleJson({
  required List<Map<String, dynamic>> slots,
}) {
  return {
    'academic_year_id': 'year-1',
    'week_start': '2026-04-07',
    'week_end': '2026-04-12',
    'slots': slots,
  };
}

Map<String, dynamic> _slotJson({
  required int day,
  String subject = 'Mathematics',
}) {
  return {
    'id': 'slot-$day-$subject',
    'day_of_week': day,
    'start_time': '08:00',
    'end_time': '09:00',
    'subject': subject,
    'teacher_id': 'teacher-1',
    'room': 'A1',
    'is_recurring': true,
    'class_id': 'class-1',
    'class_name': 'Class 6A',
  };
}

Future<void> _settle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 100));
}
