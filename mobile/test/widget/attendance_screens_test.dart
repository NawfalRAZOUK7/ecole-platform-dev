import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/attendance.dart';
import 'package:ecole_platform/features/attendance/attendance_history_screen.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  group('Attendance screens', () {
    setUpAll(registerTestFallbacks);

    testWidgets('AttendanceHistoryScreen shows a loader while classes resolve',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final attendanceRepository = MockAttendanceRepository();
      final completer = Completer<List<dynamic>>();

      when(
        () => teacherRepository.getClasses(),
      ).thenAnswer((_) => completer.future.then((value) => value.cast()));

      await pumpApp(
        tester,
        const AttendanceHistoryScreen(),
        overrides: buildMockRepositoryOverrides(
          attendanceRepository: attendanceRepository,
          teacherRepository: teacherRepository,
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('AttendanceHistoryScreen shows empty history states',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final attendanceRepository = MockAttendanceRepository();

      when(() => teacherRepository.getClasses()).thenAnswer(
        (_) async => [createClassInfo()],
      );
      when(() => teacherRepository.getClassStudents('class-1')).thenAnswer(
        (_) async => [createStudentInfo()],
      );
      when(() => attendanceRepository.getStudentHistory('student-1'))
          .thenAnswer(
        (_) async => const [],
      );

      await pumpApp(
        tester,
        const AttendanceHistoryScreen(),
        overrides: buildMockRepositoryOverrides(
          attendanceRepository: attendanceRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('No attendance history yet'), findsOneWidget);
    });

    testWidgets('AttendanceHistoryScreen renders stats and recent sessions',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final attendanceRepository = MockAttendanceRepository();

      when(() => teacherRepository.getClasses()).thenAnswer(
        (_) async => [createClassInfo()],
      );
      when(() => teacherRepository.getClassStudents('class-1')).thenAnswer(
        (_) async => [createStudentInfo()],
      );
      when(() => attendanceRepository.getStudentHistory('student-1'))
          .thenAnswer(
        (_) async => [
          AttendanceEntry.fromJson(
            const {
              'id': 'attendance-1',
              'student_id': 'student-1',
              'student_name': 'Student Example',
              'date': '2026-04-11',
              'status': 'present',
            },
          ),
          AttendanceEntry.fromJson(
            const {
              'id': 'attendance-2',
              'student_id': 'student-1',
              'student_name': 'Student Example',
              'date': '2026-04-10',
              'status': 'absent',
            },
          ),
        ],
      );

      await pumpApp(
        tester,
        const AttendanceHistoryScreen(),
        overrides: buildMockRepositoryOverrides(
          attendanceRepository: attendanceRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('Attendance history'), findsOneWidget);
      expect(find.text('Recent sessions'), findsOneWidget);
      expect(find.textContaining('50.0%'), findsOneWidget);
      expect(find.text('present'), findsWidgets);
      expect(find.text('absent'), findsWidgets);
    });

    testWidgets('AttendanceHistoryScreen exposes filter dropdowns',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final attendanceRepository = MockAttendanceRepository();

      when(() => teacherRepository.getClasses()).thenAnswer(
        (_) async => [createClassInfo()],
      );
      when(() => teacherRepository.getClassStudents('class-1')).thenAnswer(
        (_) async => [createStudentInfo()],
      );
      when(() => attendanceRepository.getStudentHistory('student-1'))
          .thenAnswer(
        (_) async => const [],
      );

      await pumpApp(
        tester,
        const AttendanceHistoryScreen(),
        overrides: buildMockRepositoryOverrides(
          attendanceRepository: attendanceRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('Class'), findsOneWidget);
      expect(find.text('Student'), findsOneWidget);
      expect(find.byType(DropdownButtonFormField<String>), findsNWidgets(2));
    });

    testWidgets('AttendanceHistoryScreen renders errors from class loading',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final attendanceRepository = MockAttendanceRepository();

      when(
        () => teacherRepository.getClasses(),
      ).thenThrow(Exception('classes failed'));

      await pumpApp(
        tester,
        const AttendanceHistoryScreen(),
        overrides: buildMockRepositoryOverrides(
          attendanceRepository: attendanceRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      expect(find.byType(AppErrorWidget), findsOneWidget);
      expect(find.textContaining('classes failed'), findsOneWidget);
    });
  });
}

Future<void> _settle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 100));
  await tester.pump(const Duration(milliseconds: 100));
}
