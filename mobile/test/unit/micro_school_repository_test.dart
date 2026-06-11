import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/data/repositories_impl/school/micro_school_repository_impl.dart';
import 'package:ecole_platform/domain/entities/school/micro_school.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_mocks.dart';

Map<String, dynamic> _schoolJson({
  String id = 'ms-1',
  String status = 'active',
}) =>
    {
      'id': id,
      'name': 'École Benani Casablanca',
      'description': 'Micro-school for CE1-CE2',
      'location': 'Quartier Maarif',
      'city': 'Casablanca',
      'capacity': 20,
      'student_count': 14,
      'status': status,
    };

Map<String, dynamic> _enrollmentJson({String id = 'enr-1'}) => {
      'id': id,
      'micro_group_id': 'grp-1',
      'child_name': 'Yassine',
      'parent_id': 'par-1',
      'date_of_birth': '2018-09-01',
      'status': 'active',
    };

Map<String, dynamic> _paymentJson({String id = 'pay-1'}) => {
      'id': id,
      'micro_school_id': 'ms-1',
      'parent_id': 'par-1',
      'child_enrollment_id': 'enr-1',
      'amount': 1500.0,
      'currency': 'MAD',
      'period_type': 'monthly',
      'period_start': '2026-05-01',
      'period_end': '2026-05-31',
      'status': 'pending',
    };

Map<String, dynamic> _resourceJson({String id = 'res-1'}) => {
      'id': id,
      'micro_school_id': 'ms-1',
      'title': 'Fiche de maths',
      'description': null,
      'resource_type': 'pdf',
      'file_path': null,
      'url': 'https://cdn.example.com/math.pdf',
      'created_at': '2026-05-01T00:00:00Z',
    };

void main() {
  late MockApiClient api;
  late MicroSchoolRepositoryImpl repo;

  setUpAll(registerTestFallbacks);

  setUp(() {
    api = MockApiClient();
    repo = MicroSchoolRepositoryImpl(api: api);
  });

  // ── listMicroSchools ──────────────────────────────────────────────────────

  group('listMicroSchools', () {
    test('returns list of MicroSchool from API', () async {
      when(() => api.list('/micro/schools', params: any(named: 'params')))
          .thenAnswer((_) async => listResponse([_schoolJson()]));

      final result = await repo.listMicroSchools();

      expect(result, hasLength(1));
      expect(result.first, isA<MicroSchool>());
      expect(result.first.name, 'École Benani Casablanca');
      expect(result.first.capacity, 20);
    });

    test('passes params to API', () async {
      when(() => api.list('/micro/schools', params: any(named: 'params')))
          .thenAnswer((_) async => listResponse([]));

      await repo.listMicroSchools(params: {'city': 'Casablanca'});

      final captured = verify(
        () => api.list('/micro/schools', params: captureAny(named: 'params')),
      ).captured.first as Map<String, dynamic>;
      expect(captured['city'], 'Casablanca');
    });

    test('returns empty list when none found', () async {
      when(() => api.list(any(), params: any(named: 'params')))
          .thenAnswer((_) async => listResponse([]));

      final result = await repo.listMicroSchools();
      expect(result, isEmpty);
    });
  });

  // ── createMicroSchool ─────────────────────────────────────────────────────

  group('createMicroSchool', () {
    test('posts payload and returns created school', () async {
      when(() => api.post('/micro/schools', body: any(named: 'body')))
          .thenAnswer((_) async => response(_schoolJson()));

      final payload = {'name': 'École Benani', 'city': 'Casablanca'};
      final result = await repo.createMicroSchool(payload);

      expect(result, isA<MicroSchool>());
      expect(result.id, 'ms-1');
      verify(() => api.post('/micro/schools', body: payload)).called(1);
    });

    test('throws on API failure', () async {
      when(() => api.post(any(), body: any(named: 'body')))
          .thenThrow(offlineError());

      expect(
        () => repo.createMicroSchool({}),
        throwsA(isA<ApiClientError>()),
      );
    });
  });

  // ── getMicroSchoolDetail ──────────────────────────────────────────────────

  group('getMicroSchoolDetail', () {
    test('returns first school matching id', () async {
      when(() => api.list('/micro/schools', params: any(named: 'params')))
          .thenAnswer((_) async => listResponse([_schoolJson()]));

      final result = await repo.getMicroSchoolDetail('ms-1');

      expect(result.id, 'ms-1');
    });

    test('returns empty school when list returns empty', () async {
      when(() => api.list('/micro/schools', params: any(named: 'params')))
          .thenAnswer((_) async => listResponse([]));

      final result = await repo.getMicroSchoolDetail('nonexistent');

      expect(result.id, 'nonexistent');
      expect(result.name, '');
    });
  });

  // ── updateMicroSchool ─────────────────────────────────────────────────────

  group('updateMicroSchool', () {
    test('puts payload and returns updated school', () async {
      when(() => api.put('/micro/schools/ms-1', body: any(named: 'body')))
          .thenAnswer((_) async => response(_schoolJson(status: 'inactive')));

      final result =
          await repo.updateMicroSchool('ms-1', {'status': 'inactive'});

      expect(result.status, 'inactive');
    });
  });

  // ── deleteMicroSchool ─────────────────────────────────────────────────────

  group('deleteMicroSchool', () {
    test('puts status closed to soft-delete the school', () async {
      when(() => api.put('/micro/schools/ms-1', body: any(named: 'body')))
          .thenAnswer((_) async => response(_schoolJson(status: 'closed')));

      await repo.deleteMicroSchool('ms-1');

      final body = verify(
        () => api.put('/micro/schools/ms-1', body: captureAny(named: 'body')),
      ).captured.first as Map<String, dynamic>;
      expect(body['status'], 'closed');
    });
  });

  // ── getEnrollments ────────────────────────────────────────────────────────

  group('getEnrollments', () {
    test('returns list of enrollments for school', () async {
      when(
        () => api.list('/micro/enrollments', params: any(named: 'params')),
      ).thenAnswer((_) async => listResponse([_enrollmentJson()]));

      final result = await repo.getEnrollments('ms-1');

      expect(result, hasLength(1));
      expect(result.first, isA<MicroEnrollment>());
      expect(result.first.childName, 'Yassine');
    });

    test('passes micro_school_id filter', () async {
      when(
        () => api.list('/micro/enrollments', params: any(named: 'params')),
      ).thenAnswer((_) async => listResponse([]));

      await repo.getEnrollments('ms-1');

      final params = verify(
        () =>
            api.list('/micro/enrollments', params: captureAny(named: 'params')),
      ).captured.first as Map<String, dynamic>;
      expect(params['micro_school_id'], 'ms-1');
    });
  });

  // ── enrollStudent ─────────────────────────────────────────────────────────

  group('enrollStudent', () {
    test('fetches groups then posts enrollment', () async {
      // getGroups call (uses /micro/schools/{id}/groups, no params)
      when(
        () => api.list('/micro/schools/ms-1/groups'),
      ).thenAnswer(
        (_) async => listResponse([
          {'id': 'grp-1', 'name': 'Group A'},
        ]),
      );
      when(() => api.post('/micro/enrollments', body: any(named: 'body')))
          .thenAnswer((_) async => response(_enrollmentJson()));

      final result = await repo.enrollStudent('ms-1', {
        'student_name': 'Yassine',
        'date_of_birth': '2018-09-01',
      });

      expect(result, isA<MicroEnrollment>());
      expect(result.childName, 'Yassine');
    });
  });

  // ── unenrollStudent ───────────────────────────────────────────────────────

  group('unenrollStudent', () {
    test('deletes the enrollment', () async {
      when(() => api.delete('/micro/schools/ms-1/enrollments/enr-1'))
          .thenAnswer((_) async => response({}));

      await repo.unenrollStudent('ms-1', 'enr-1');

      verify(() => api.delete('/micro/schools/ms-1/enrollments/enr-1'))
          .called(1);
    });
  });

  // ── getPayments ───────────────────────────────────────────────────────────

  group('getPayments', () {
    test('returns payments for a micro school', () async {
      when(
        () => api.list('/micro/payments', params: any(named: 'params')),
      ).thenAnswer((_) async => listResponse([_paymentJson()]));

      final result = await repo.getPayments('ms-1');

      expect(result, hasLength(1));
      expect(result.first, isA<MicroPayment>());
      expect(result.first.amount, 1500.0);
    });
  });

  // ── createPayment ─────────────────────────────────────────────────────────

  group('createPayment', () {
    test('posts payment and returns created entry', () async {
      when(() => api.post('/micro/payments', body: any(named: 'body')))
          .thenAnswer((_) async => response(_paymentJson()));

      final result = await repo.createPayment('ms-1', {
        'amount': 1500.0,
        'period_type': 'monthly',
        'period_start': '2026-05-01',
        'period_end': '2026-05-31',
      });

      expect(result.amount, 1500.0);
      expect(result.currency, 'MAD');
    });
  });

  // ── getResources ──────────────────────────────────────────────────────────

  group('getResources', () {
    test('returns list of resources for school', () async {
      when(
        () => api.list('/micro/resources', params: any(named: 'params')),
      ).thenAnswer((_) async => listResponse([_resourceJson()]));

      final result = await repo.getResources('ms-1');

      expect(result, hasLength(1));
      expect(result.first, isA<MicroResource>());
      expect(result.first.title, 'Fiche de maths');
    });
  });
}
