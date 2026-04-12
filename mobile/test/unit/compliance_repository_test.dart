import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/data/repositories_impl/compliance_repository_impl.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  test('lists MEN curricula', () async {
    final api = MockApiClient();
    final repository = ComplianceRepositoryImpl(api: api);

    when(
      () => api.list('/compliance/curricula', params: null),
    ).thenAnswer(
      (_) async => listResponse(
        const [
          {
            'id': 'curriculum-1',
            'title': 'Mathematics grade 6',
            'subject': 'Mathematics',
            'grade': '6A',
          },
        ],
      ),
    );

    final curricula = await repository.listCurricula();

    expect(curricula.single.subject, 'Mathematics');
  });

  test('lists curriculum mappings', () async {
    final api = MockApiClient();
    final repository = ComplianceRepositoryImpl(api: api);

    when(
      () => api.list('/compliance/mappings', params: null),
    ).thenAnswer(
      (_) async => listResponse(
        const [
          {
            'id': 'mapping-1',
            'curriculum_id': 'curriculum-1',
            'course_id': 'course-1',
          },
        ],
      ),
    );

    final mappings = await repository.listMappings();

    expect(mappings.single.courseId, 'course-1');
  });

  test('lists generated compliance reports', () async {
    final api = MockApiClient();
    final repository = ComplianceRepositoryImpl(api: api);

    when(
      () => api.list('/compliance/reports', params: null),
    ).thenAnswer(
      (_) async => listResponse(
        const [
          {
            'id': 'report-1',
            'title': 'Coverage report',
            'status': 'ready',
            'created_at': '2026-04-12T09:00:00Z',
          },
        ],
      ),
    );

    final reports = await repository.listReports();

    expect(reports.single.status, 'ready');
  });
}
