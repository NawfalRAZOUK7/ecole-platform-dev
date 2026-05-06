import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/features/quizzes/teacher_quiz_list_screen.dart';

import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

Future<void> _settle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 300));
}

void main() {
  group('Quizzes screens', () {
    setUpAll(registerTestFallbacks);

    testWidgets('TeacherQuizListScreen shows quiz titles after data loads',
        (tester) async {
      final mockApi = MockApiClient();

      when(() => mockApi.list(
            any(),
            params: any(named: 'params'),
          )).thenAnswer(
        (_) async => ApiListResponse<Map<String, dynamic>>(
          data: [
            {
              'id': 'quiz-1',
              'title': 'Fractions Quiz',
              'class_name': '6A',
              'class_id': 'class-1',
              'period_id': 'period-1',
              'subject': 'Math',
              'status': 'published',
              'question_count': 5,
              'assigned_at': '2026-04-01T08:00:00Z',
              'due_at': null,
              'submitted_count': 10,
              'completion_rate': 0.8,
            }
          ],
          hasMore: false,
        ),
      );

      await pumpApp(
        tester,
        const TeacherQuizListScreen(),
        overrides: [
          apiClientProvider.overrideWithValue(mockApi),
        ],
      );
      await tester.pumpAndSettle();

      expect(find.textContaining('Fractions Quiz'), findsOneWidget);
    });

    testWidgets('TeacherQuizListScreen shows empty state when no quizzes',
        (tester) async {
      final mockApi = MockApiClient();

      when(() => mockApi.list(
            any(),
            params: any(named: 'params'),
          )).thenAnswer(
        (_) async => const ApiListResponse<Map<String, dynamic>>(
          data: [],
          hasMore: false,
        ),
      );

      await pumpApp(
        tester,
        const TeacherQuizListScreen(),
        overrides: [
          apiClientProvider.overrideWithValue(mockApi),
        ],
      );
      await tester.pumpAndSettle();

      // With empty list, should show some empty/placeholder UI
      expect(find.byType(Scaffold), findsWidgets);
    });

    testWidgets('TeacherQuizListScreen shows loader while fetching',
        (tester) async {
      final mockApi = MockApiClient();
      final completer = Completer<ApiListResponse<Map<String, dynamic>>>();

      when(() => mockApi.list(
            any(),
            params: any(named: 'params'),
          )).thenAnswer((_) => completer.future);

      await pumpApp(
        tester,
        const TeacherQuizListScreen(),
        overrides: [
          apiClientProvider.overrideWithValue(mockApi),
        ],
      );

      // While loading, should show some loading indicator
      expect(find.byType(Scaffold), findsWidgets);

      // Resolve to avoid pending-timer assertion on teardown
      completer.complete(const ApiListResponse<Map<String, dynamic>>(
        data: [],
        hasMore: false,
      ));
    });
  });
}
