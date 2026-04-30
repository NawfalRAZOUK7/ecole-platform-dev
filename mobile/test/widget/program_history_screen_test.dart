import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/program.dart';
import 'package:ecole_platform/features/student/program_history_screen.dart';

import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  testWidgets(
    'AcademicHistoryScreen renders transcript tools and academic snapshots',
    (tester) async {
      final repository = MockProgramRepository();
      when(() => repository.getCurrentProgram('student-1')).thenAnswer(
        (_) async => const CurrentProgram(
          studentId: 'student-1',
          academicYearId: 'ay-1',
          enrollmentId: 'enr-1',
          program: ProgramSummary(
            id: 'prog-1',
            code: 'SCI-MATH',
            name: 'Sciences Mathématiques',
            versionLabel: '1.0',
          ),
        ),
      );
      when(() => repository.getAcademicTimeline('student-1')).thenAnswer(
        (_) async => const [
          AcademicTimelineEntry(
            enrollmentId: 'enr-1',
            academicYearId: 'ay-1',
            academicYearLabel: '2026-2027',
            academicYearStart: '2026-09-01',
            academicYearEnd: '2027-07-15',
            periodId: 'p-1',
            periodLabel: 'Trimester 1',
            periodStart: '2026-09-01',
            periodEnd: '2026-12-20',
            classId: 'cls-1',
            classCode: '3A',
            className: 'Classe 3A',
            status: 'active',
          ),
        ],
      );
      when(() => repository.getProgramHistory('student-1')).thenAnswer(
        (_) async => const [],
      );
      when(() => repository.getStudentSnapshots('student-1')).thenAnswer(
        (_) async => const [
          AcademicSnapshotSummary(
            id: 'snap-1',
            schoolId: 'school-1',
            studentId: 'student-1',
            academicYearId: 'ay-1',
            snapshotKind: 'YEAR_END',
            takenAt: '2026-07-01T10:00:00Z',
            takenBy: 'user-1',
          ),
        ],
      );

      await pumpApp(
        tester,
        const AcademicHistoryScreen(studentId: 'student-1'),
        overrides: buildMockRepositoryOverrides(programRepository: repository),
        localeCode: 'en',
      );
      await tester.pumpAndSettle();

      expect(find.text('Transcript PDF'), findsOneWidget);
      expect(
        find.text('Academic snapshots', skipOffstage: false),
        findsOneWidget,
      );
      expect(find.text('2026-2027'), findsWidgets);
      expect(find.text('Year End', skipOffstage: false), findsOneWidget);
      expect(
        find.text('Open snapshot PDF', skipOffstage: false),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    'AcademicHistoryScreen shows transcript helper text when no academic year exists',
    (tester) async {
      final repository = MockProgramRepository();
      when(() => repository.getCurrentProgram('student-2')).thenAnswer(
        (_) async => const CurrentProgram(studentId: 'student-2'),
      );
      when(() => repository.getAcademicTimeline('student-2')).thenAnswer(
        (_) async => const [],
      );
      when(() => repository.getProgramHistory('student-2')).thenAnswer(
        (_) async => const [],
      );
      when(() => repository.getStudentSnapshots('student-2')).thenAnswer(
        (_) async => const [],
      );

      await pumpApp(
        tester,
        const AcademicHistoryScreen(studentId: 'student-2'),
        overrides: buildMockRepositoryOverrides(programRepository: repository),
        localeCode: 'en',
      );
      await tester.pumpAndSettle();

      expect(
        find.text('No academic year is available for transcript export.'),
        findsOneWidget,
      );
      expect(
        find.text(
          'No academic snapshots available yet.',
          skipOffstage: false,
        ),
        findsOneWidget,
      );
    },
  );
}
