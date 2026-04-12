import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/micro_school.dart';
import 'package:ecole_platform/features/micro-schools/micro_school_detail_screen.dart';
import 'package:ecole_platform/features/micro-schools/micro_school_list_screen.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  testWidgets('MicroSchoolListScreen renders school cards', (tester) async {
    final repository = MockMicroSchoolRepository();
    when(() => repository.listMicroSchools()).thenAnswer(
      (_) async => [_school],
    );

    await pumpApp(
      tester,
      const MicroSchoolListScreen(),
      overrides: buildMockRepositoryOverrides(
        microSchoolRepository: repository,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Casablanca Hub'), findsOneWidget);
    expect(find.text('capacity'), findsNothing);
  });

  testWidgets('MicroSchoolListScreen shows an empty state', (tester) async {
    final repository = MockMicroSchoolRepository();
    when(() => repository.listMicroSchools()).thenAnswer(
      (_) async => const [],
    );

    await pumpApp(
      tester,
      const MicroSchoolListScreen(),
      overrides: buildMockRepositoryOverrides(
        microSchoolRepository: repository,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(AppEmptyState), findsOneWidget);
  });

  testWidgets('MicroSchoolDetailScreen renders details and enrollment action',
      (tester) async {
    final repository = MockMicroSchoolRepository();
    when(() => repository.getMicroSchoolDetail('school-1')).thenAnswer(
      (_) async => _school,
    );
    when(() => repository.getEnrollments('school-1')).thenAnswer(
      (_) async => const [
        MicroEnrollment(
          id: 'enrollment-1',
          microSchoolId: 'school-1',
          childName: 'Student Example',
          status: 'active',
        ),
      ],
    );
    when(() => repository.getResources('school-1')).thenAnswer(
      (_) async => const [
        MicroResource(
          id: 'resource-1',
          microSchoolId: 'school-1',
          title: 'Math kit',
          description: 'Learning resources',
          resourceType: 'kit',
          language: 'fr',
        ),
      ],
    );
    when(() => repository.getPayments('school-1')).thenAnswer(
      (_) async => const [
        MicroPayment(
          id: 'payment-1',
          microSchoolId: 'school-1',
          amount: 500,
          currency: 'MAD',
          status: 'paid',
        ),
      ],
    );
    when(() => repository.getProgress('school-1')).thenAnswer(
      (_) async => const MicroProgressOverview(
        averageProgress: 82,
        activeStudents: 12,
        completionRate: 75,
        series: [
          MicroMetricPoint(label: 'Week 1', value: 70),
        ],
      ),
    );

    await pumpApp(
      tester,
      const MicroSchoolDetailScreen(schoolId: 'school-1'),
      overrides: buildMockRepositoryOverrides(
        microSchoolRepository: repository,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Casablanca Hub'), findsOneWidget);
    expect(find.byIcon(Icons.person_add_alt_1), findsOneWidget);
    expect(find.text('Student Example'), findsOneWidget);
  });
}

const _school = MicroSchool(
  id: 'school-1',
  name: 'Casablanca Hub',
  description: 'A neighborhood micro-school.',
  location: 'Maarif',
  city: 'Casablanca',
  capacity: 40,
  studentCount: 28,
  status: 'active',
);
