import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/skills.dart';
import 'package:ecole_platform/features/skills/skill_analytics_screen.dart';
import 'package:ecole_platform/features/skills/skill_evaluation_screen.dart';
import 'package:ecole_platform/features/skills/skill_passport_screen.dart';
import 'package:ecole_platform/features/skills/skills_overview_screen.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import '../helpers/factories.dart';
import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  group('Skills screens', () {
    setUpAll(registerTestFallbacks);

    testWidgets('SkillsOverviewScreen shows empty states with no dimensions',
        (tester) async {
      final skillsRepository = MockSkillsRepository();

      when(
        () => skillsRepository.getSchoolAnalytics(
          academicYearId: any(named: 'academicYearId'),
        ),
      ).thenAnswer(
        (_) async => const SkillSchoolAnalytics(
          overallScore: 0,
          dimensions: [],
        ),
      );

      await pumpApp(
        tester,
        const SkillsOverviewScreen(),
        overrides: buildMockRepositoryOverrides(
          skillsRepository: skillsRepository,
        ),
      );
      await _settle(tester);

      expect(find.byType(AppEmptyState), findsOneWidget);
    });

    testWidgets('SkillsOverviewScreen renders dimension summaries',
        (tester) async {
      final skillsRepository = MockSkillsRepository();

      when(
        () => skillsRepository.getSchoolAnalytics(
          academicYearId: any(named: 'academicYearId'),
        ),
      ).thenAnswer((_) async => _schoolAnalytics);

      await pumpApp(
        tester,
        const SkillsOverviewScreen(),
        overrides: buildMockRepositoryOverrides(
          skillsRepository: skillsRepository,
        ),
      );
      await _settle(tester);
      await tester.scrollUntilVisible(
        find.text('Collaboration'),
        200,
        scrollable: find.byType(Scrollable).first,
      );

      expect(find.text('Creativity'), findsOneWidget);
      expect(find.text('Collaboration'), findsOneWidget);
      expect(find.text('88.0'), findsWidgets);
    });

    testWidgets('SkillAnalyticsScreen renders classes and leaderboard',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final skillsRepository = MockSkillsRepository();

      when(() => teacherRepository.getClasses()).thenAnswer(
        (_) async => [createClassInfo()],
      );
      when(
        () => skillsRepository.getClassAnalytics(
          'class-1',
          academicYearId: any(named: 'academicYearId'),
        ),
      ).thenAnswer((_) async => _classAnalytics);
      when(
        () => skillsRepository.getLeaderboard(
          'class-1',
          academicYearId: any(named: 'academicYearId'),
          limit: any(named: 'limit'),
        ),
      ).thenAnswer((_) async => _leaderboard);

      await pumpApp(
        tester,
        const SkillAnalyticsScreen(),
        overrides: buildMockRepositoryOverrides(
          skillsRepository: skillsRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('Class 6A'), findsOneWidget);
      expect(find.text('Student Example'), findsOneWidget);
      expect(find.text('95.0'), findsWidgets);
    });

    testWidgets('SkillAnalyticsScreen shows empty class states',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final skillsRepository = MockSkillsRepository();

      when(() => teacherRepository.getClasses())
          .thenAnswer((_) async => const []);

      await pumpApp(
        tester,
        const SkillAnalyticsScreen(),
        overrides: buildMockRepositoryOverrides(
          skillsRepository: skillsRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      expect(find.byType(AppEmptyState), findsOneWidget);
    });

    testWidgets('SkillEvaluationScreen evaluates selected students',
        (tester) async {
      final teacherRepository = MockTeacherRepository();
      final skillsRepository = MockSkillsRepository();

      when(() => teacherRepository.getClasses()).thenAnswer(
        (_) async => [createClassInfo()],
      );
      when(() => teacherRepository.getClassStudents('class-1')).thenAnswer(
        (_) async => [createStudentInfo()],
      );
      when(
        () => skillsRepository.evaluateStudent(
          'student-1',
          academicYearId: any(named: 'academicYearId'),
        ),
      ).thenAnswer((_) async => _evaluation);

      await pumpApp(
        tester,
        const SkillEvaluationScreen(),
        overrides: buildMockRepositoryOverrides(
          skillsRepository: skillsRepository,
          teacherRepository: teacherRepository,
        ),
      );
      await _settle(tester);

      await tester.tap(find.byIcon(Icons.fact_check_outlined));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 100));

      verify(
        () => skillsRepository.evaluateStudent(
          'student-1',
          academicYearId: any(named: 'academicYearId'),
        ),
      ).called(1);
      expect(find.text('Creativity'), findsOneWidget);
      expect(find.text('94.0'), findsWidgets);
      expect(find.text('92.0'), findsWidgets);
    });

    testWidgets('SkillPassportScreen renders passport content', (tester) async {
      final skillsRepository = MockSkillsRepository();

      when(
        () => skillsRepository.getPassport(
          'student-1',
          academicYearId: any(named: 'academicYearId'),
        ),
      ).thenAnswer((_) async => _passport);

      await pumpApp(
        tester,
        const SkillPassportScreen(studentId: 'student-1'),
        overrides: buildMockRepositoryOverrides(
          skillsRepository: skillsRepository,
        ),
      );
      await _settle(tester);

      expect(find.text('Student Example'), findsOneWidget);
      expect(find.text('Creativity'), findsOneWidget);
      expect(find.text('88.0'), findsWidgets);
    });

    testWidgets('SkillPassportScreen renders repository errors',
        (tester) async {
      final skillsRepository = MockSkillsRepository();

      when(
        () => skillsRepository.getPassport(
          'student-1',
          academicYearId: any(named: 'academicYearId'),
        ),
      ).thenThrow(Exception('passport failed'));

      await pumpApp(
        tester,
        const SkillPassportScreen(studentId: 'student-1'),
        overrides: buildMockRepositoryOverrides(
          skillsRepository: skillsRepository,
        ),
      );
      await _settle(tester);

      expect(find.byType(AppErrorWidget), findsOneWidget);
      expect(find.textContaining('passport failed'), findsOneWidget);
    });
  });
}

const _schoolAnalytics = SkillSchoolAnalytics(
  overallScore: 88.0,
  dimensions: [
    SkillScoreItem(id: 'skill-1', label: 'Creativity', score: 91.0),
    SkillScoreItem(id: 'skill-2', label: 'Collaboration', score: 85.0),
    SkillScoreItem(id: 'skill-3', label: 'Leadership', score: 88.0),
  ],
);

const _classAnalytics = SkillClassAnalytics(
  classId: 'class-1',
  averageScore: 86.0,
  studentCount: 24,
  dimensions: [
    SkillScoreItem(id: 'skill-1', label: 'Creativity', score: 90.0),
  ],
);

const _leaderboard = [
  SkillLeaderboardEntry(
    studentId: 'student-1',
    studentName: 'Student Example',
    score: 95.0,
  ),
];

const _evaluation = SkillEvaluation(
  studentId: 'student-1',
  overallScore: 92.0,
  summary: 'Strong creative thinking',
  dimensions: [
    SkillScoreItem(id: 'skill-1', label: 'Creativity', score: 94.0),
  ],
);

const _passport = SkillPassport(
  studentId: 'student-1',
  studentName: 'Student Example',
  academicYearId: '2026',
  overallScore: 88.0,
  dimensions: [
    SkillScoreItem(id: 'skill-1', label: 'Creativity', score: 91.0),
  ],
);

Future<void> _settle(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 100));
  await tester.pump(const Duration(milliseconds: 100));
}
