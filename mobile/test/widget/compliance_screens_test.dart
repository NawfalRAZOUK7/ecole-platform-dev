import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/admin/compliance.dart';
import 'package:ecole_platform/features/admin/compliance/compliance_dashboard_screen.dart';
import 'package:ecole_platform/features/admin/compliance/curriculum_mapping_screen.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  testWidgets('ComplianceDashboardScreen renders dashboard metrics',
      (tester) async {
    final repository = MockComplianceRepository();
    when(
      () => repository.getDashboard(
        academicYearId: any(named: 'academicYearId'),
      ),
    ).thenAnswer((_) async => _dashboard);

    await pumpApp(
      tester,
      const ComplianceDashboardScreen(),
      overrides: buildMockRepositoryOverrides(complianceRepository: repository),
    );
    await tester.pumpAndSettle();

    expect(find.text('Coverage gap'), findsOneWidget);
    expect(find.text('61%'), findsWidgets);
  });

  testWidgets('CurriculumMappingScreen renders curricula and mappings',
      (tester) async {
    final repository = MockComplianceRepository();
    when(() => repository.listCurricula()).thenAnswer(
      (_) async => [_curriculum],
    );
    when(() => repository.listMappings()).thenAnswer(
      (_) async => [_mapping],
    );

    await pumpApp(
      tester,
      const CurriculumMappingScreen(),
      overrides: buildMockRepositoryOverrides(complianceRepository: repository),
    );
    await tester.pumpAndSettle();

    expect(find.text('Mathematics grade 6'), findsOneWidget);
    expect(find.text('course-1'), findsOneWidget);
  });

  testWidgets('CurriculumMappingScreen shows empty mappings state',
      (tester) async {
    final repository = MockComplianceRepository();
    when(() => repository.listCurricula()).thenAnswer(
      (_) async => [_curriculum],
    );
    when(() => repository.listMappings()).thenAnswer(
      (_) async => const [],
    );

    await pumpApp(
      tester,
      const CurriculumMappingScreen(),
      overrides: buildMockRepositoryOverrides(complianceRepository: repository),
    );
    await tester.pumpAndSettle();

    expect(find.byType(AppEmptyState), findsOneWidget);
  });
}

const _dashboard = ComplianceDashboardData(
  coverageRate: 61,
  objectivesCoveredRate: 74,
  missingCoverageRate: 39,
  metrics: [
    ComplianceMetric(label: 'Coverage gap', value: 61),
  ],
);

const _curriculum = MenCurriculum(
  id: 'curriculum-1',
  title: 'Mathematics grade 6',
  subject: 'Mathematics',
  grade: '6A',
);

const _mapping = CurriculumMapping(
  id: 'mapping-1',
  curriculumId: 'curriculum-1',
  courseId: 'course-1',
);
