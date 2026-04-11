import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/gradebook.dart';
import 'package:ecole_platform/features/gradebook/grade_detail_screen.dart';
import 'package:ecole_platform/features/gradebook/gradebook_screen.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  group('Gradebook screens', () {
    setUpAll(registerTestFallbacks);

    testWidgets('GradebookScreen shows skeleton while classes load',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final gradebookRepository = MockGradebookRepository();
      final completer = Completer<List<dynamic>>();

      when(
        () => teacherRepository.getClasses(),
      ).thenAnswer((_) => completer.future.then((value) => value.cast()));

      await pumpApp(
        tester,
        const GradebookScreen(),
        overrides: buildMockRepositoryOverrides(
          gradebookRepository: gradebookRepository,
          teacherRepository: teacherRepository,
        ),
      );

      expect(find.byType(AppSkeleton), findsOneWidget);
    });

    testWidgets('GradebookScreen renders classes and grade cells',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final gradebookRepository = MockGradebookRepository();

      when(() => teacherRepository.getClasses()).thenAnswer(
        (_) async => [createClassInfo()],
      );
      when(() => gradebookRepository.getClassGradebook('class-1')).thenAnswer(
        (_) async => const GradebookGrid(
          classId: 'class-1',
          className: '6A',
          columns: [
            GradebookColumn(
              assessmentId: 'assessment-1',
              title: 'Quiz 1',
              weight: 0.4,
              date: '2026-04-10',
              type: 'quiz',
            ),
          ],
          entries: [
            GradebookEntry(
              studentId: 'student-1',
              studentName: 'Student Example',
              grades: {'assessment-1': 15.5},
              weightedAverage: 15.5,
            ),
          ],
        ),
      );
      when(() => gradebookRepository.exportGrades(any(), format: any(named: 'format')))
          .thenAnswer((_) async => null);
      when(() => gradebookRepository.updateGrades(any()))
          .thenAnswer((_) async {});

      await pumpApp(
        tester,
        const GradebookScreen(),
        overrides: buildMockRepositoryOverrides(
          gradebookRepository: gradebookRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('Quiz 1'), findsOneWidget);
      expect(find.text('Student Example'), findsOneWidget);
      expect(find.byType(TextFormField), findsOneWidget);
    });

    testWidgets('GradebookScreen shows empty states for empty grids',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final gradebookRepository = MockGradebookRepository();

      when(() => teacherRepository.getClasses()).thenAnswer(
        (_) async => [createClassInfo()],
      );
      when(() => gradebookRepository.getClassGradebook('class-1')).thenAnswer(
        (_) async => const GradebookGrid(
          classId: 'class-1',
          className: '6A',
        ),
      );
      when(() => gradebookRepository.exportGrades(any(), format: any(named: 'format')))
          .thenAnswer((_) async => null);
      when(() => gradebookRepository.updateGrades(any()))
          .thenAnswer((_) async {});

      await pumpApp(
        tester,
        const GradebookScreen(),
        overrides: buildMockRepositoryOverrides(
          gradebookRepository: gradebookRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      expect(find.byType(AppEmptyState), findsOneWidget);
    });

    testWidgets('GradebookScreen exports grades through the repository',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final gradebookRepository = MockGradebookRepository();

      when(() => teacherRepository.getClasses()).thenAnswer(
        (_) async => [createClassInfo()],
      );
      when(() => gradebookRepository.getClassGradebook('class-1')).thenAnswer(
        (_) async => const GradebookGrid(
          classId: 'class-1',
          className: '6A',
          columns: [
            GradebookColumn(
              assessmentId: 'assessment-1',
              title: 'Quiz 1',
              weight: 0.4,
              date: '2026-04-10',
              type: 'quiz',
            ),
          ],
          entries: [
            GradebookEntry(
              studentId: 'student-1',
              studentName: 'Student Example',
              grades: {'assessment-1': 15.5},
              weightedAverage: 15.5,
            ),
          ],
        ),
      );
      when(() => gradebookRepository.exportGrades('class-1', format: 'csv'))
          .thenAnswer((_) async => 'https://files.ecole.test/grades.csv');
      when(() => gradebookRepository.updateGrades(any()))
          .thenAnswer((_) async {});

      await pumpApp(
        tester,
        const GradebookScreen(),
        overrides: buildMockRepositoryOverrides(
          gradebookRepository: gradebookRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      await tester.tap(find.byIcon(Icons.download_outlined));
      await tester.pumpAndSettle();

      verify(() => gradebookRepository.exportGrades('class-1', format: 'csv'))
          .called(1);
    });

    testWidgets('GradebookScreen saves edited grades', (tester) async {
      final teacherRepository = MockTeacherRepository();
      final gradebookRepository = MockGradebookRepository();

      when(() => teacherRepository.getClasses()).thenAnswer(
        (_) async => [createClassInfo()],
      );
      when(() => gradebookRepository.getClassGradebook('class-1')).thenAnswer(
        (_) async => const GradebookGrid(
          classId: 'class-1',
          className: '6A',
          columns: [
            GradebookColumn(
              assessmentId: 'assessment-1',
              title: 'Quiz 1',
              weight: 0.4,
              date: '2026-04-10',
              type: 'quiz',
            ),
          ],
          entries: [
            GradebookEntry(
              studentId: 'student-1',
              studentName: 'Student Example',
              grades: {'assessment-1': 15.5},
              weightedAverage: 15.5,
            ),
          ],
        ),
      );
      when(() => gradebookRepository.exportGrades(any(), format: any(named: 'format')))
          .thenAnswer((_) async => null);
      when(() => gradebookRepository.updateGrades(any()))
          .thenAnswer((_) async {});

      await pumpApp(
        tester,
        const GradebookScreen(),
        overrides: buildMockRepositoryOverrides(
          gradebookRepository: gradebookRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      await tester.enterText(find.byType(TextFormField), '18.0');
      await tester.tap(find.byIcon(Icons.save_outlined));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      final captured = verify(
        () => gradebookRepository.updateGrades(captureAny()),
      ).captured.single as BulkGradeUpdate;

      expect(captured.classId, 'class-1');
      expect(captured.grades.single.value, 18.0);
      expect(find.byType(SnackBar), findsOneWidget);
    });

    testWidgets('GradeDetailScreen renders assessment detail cards',
        (tester) async {
      final gradebookRepository = MockGradebookRepository();

      when(() => gradebookRepository.getStudentGrades('student-1')).thenAnswer(
        (_) async => const StudentGradeDetail(
          studentId: 'student-1',
          studentName: 'Student Example',
          classId: 'class-1',
          className: '6A',
          weightedAverage: 16.0,
          assessments: [
            StudentAssessmentGrade(
              assessmentId: 'assessment-1',
              title: 'Quiz 1',
              type: 'quiz',
              date: '2026-04-10',
              weight: 0.4,
              score: 16.0,
            ),
          ],
        ),
      );

      await pumpApp(
        tester,
        const GradeDetailScreen(studentId: 'student-1'),
        overrides: buildMockRepositoryOverrides(
          gradebookRepository: gradebookRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('Student Example'), findsOneWidget);
      expect(find.text('Quiz 1'), findsWidgets);
      expect(find.text('16.0'), findsWidgets);
    });

    testWidgets('GradeDetailScreen renders repository errors', (tester) async {
      final gradebookRepository = MockGradebookRepository();

      when(
        () => gradebookRepository.getStudentGrades('student-1'),
      ).thenThrow(Exception('detail failed'));

      await pumpApp(
        tester,
        const GradeDetailScreen(studentId: 'student-1'),
        overrides: buildMockRepositoryOverrides(
          gradebookRepository: gradebookRepository,
        ),
      );
      await _settle(tester);

      expect(find.byType(AppErrorWidget), findsOneWidget);
      expect(find.textContaining('detail failed'), findsOneWidget);
    });
  });
}

Future<void> _settle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 100));
  await tester.pump(const Duration(milliseconds: 100));
}
