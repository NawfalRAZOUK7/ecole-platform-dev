import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/domain/entities/school/micro_school.dart';
import 'package:ecole_platform/domain/repositories/school/micro_school_repository.dart';

class MicroSchoolRepositoryImpl implements MicroSchoolRepository {
  final ApiClient _api;

  MicroSchoolRepositoryImpl({required ApiClient api}) : _api = api;

  @override
  Future<List<MicroSchool>> listMicroSchools({
    Map<String, dynamic>? params,
  }) async {
    final response = await _api.list('/micro/schools', params: params);
    return response.data.map(MicroSchool.fromJson).toList();
  }

  @override
  Future<MicroSchool> createMicroSchool(Map<String, dynamic> payload) async {
    final response = await _api.post('/micro/schools', body: payload);
    return MicroSchool.fromJson(response.data);
  }

  @override
  Future<MicroSchool> getMicroSchoolDetail(String id) async {
    final items = await listMicroSchools(params: {'id': id});
    return items.isEmpty
        ? MicroSchool(
            id: id,
            name: '',
            description: '',
            location: '',
            city: '',
            capacity: 0,
            studentCount: 0,
            status: 'active',
          )
        : items.first;
  }

  @override
  Future<MicroSchool> updateMicroSchool(
    String id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.put('/micro/schools/$id', body: payload);
    return MicroSchool.fromJson(response.data);
  }

  @override
  Future<void> deleteMicroSchool(String id) async {
    await _api.put(
      '/micro/schools/$id',
      body: {
        'status': 'closed',
        'id': id,
      },
    );
  }

  @override
  Future<List<MicroEnrollment>> getEnrollments(String id) async {
    final response = await _api.list(
      '/micro/enrollments',
      params: {'micro_school_id': id},
    );
    return response.data.map(MicroEnrollment.fromJson).toList();
  }

  @override
  Future<MicroEnrollment> enrollStudent(
    String id,
    Map<String, dynamic> payload,
  ) async {
    final groups = await getGroups(id);
    final response = await _api.post(
      '/micro/enrollments',
      body: {
        'micro_group_id': groups.isEmpty ? id : groups.first['id'],
        'child_name': payload['student_name'],
        'parent_id': '00000000-0000-0000-0000-000000000000',
        'date_of_birth': payload['date_of_birth'] ?? '2020-01-01',
        'status': payload['status'] ?? 'active',
      },
    );
    return MicroEnrollment.fromJson(response.data);
  }

  @override
  Future<void> unenrollStudent(String id, String enrollmentId) async {
    await _api.delete('/micro/schools/$id/enrollments/$enrollmentId');
  }

  @override
  Future<List<MicroPayment>> getPayments(String id) async {
    final response = await _api.list(
      '/micro/payments',
      params: {'micro_school_id': id},
    );
    return response.data.map(MicroPayment.fromJson).toList();
  }

  @override
  Future<MicroPayment> createPayment(
    String id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post(
      '/micro/payments',
      body: {
        'micro_school_id': id,
        'parent_id': '00000000-0000-0000-0000-000000000000',
        'child_enrollment_id': '00000000-0000-0000-0000-000000000000',
        'amount': payload['amount'],
        'currency': 'MAD',
        'period_type': payload['period_type'] ?? 'monthly',
        'period_start': payload['period_start'] ??
            DateTime.now().toIso8601String().split('T').first,
        'period_end': payload['period_end'] ??
            DateTime.now().toIso8601String().split('T').first,
        'status': payload['status'] ?? 'pending',
      },
    );
    return MicroPayment.fromJson(response.data);
  }

  @override
  Future<List<MicroResource>> getResources(String id) async {
    final response = await _api.list(
      '/micro/resources',
      params: {'micro_school_id': id},
    );
    return response.data.map(MicroResource.fromJson).toList();
  }

  @override
  Future<MicroResource> addResource(
    String id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post(
      '/micro/resources',
      body: {
        'micro_school_id': id,
        'title': payload['title'],
        'description': payload['description'],
        'resource_type': payload['type'],
        'age_group': payload['age_group'] ?? 'all',
        'language': payload['language'] ?? 'fr',
        'file_url': payload['file_url'],
        'is_premium': payload['is_premium'] ?? false,
      },
    );
    return MicroResource.fromJson(response.data);
  }

  @override
  Future<MicroProgressOverview> getProgress(String id) async {
    final response = await _api.list(
      '/micro/progress-logs',
      params: {'micro_school_id': id},
    );
    final studentIds = response.data
        .map((item) => item['student_id']?.toString())
        .whereType<String>()
        .toSet();
    return MicroProgressOverview(
      averageProgress: response.data.isEmpty ? 0 : 100,
      activeStudents: studentIds.length,
      completionRate: response.data.isEmpty ? 0 : 100,
      series: response.data
          .map(
            (item) => MicroMetricPoint(
              label: item['date']?.toString() ?? '',
              value: 1,
            ),
          )
          .toList(),
    );
  }

  @override
  Future<MicroStudentProgress> getStudentProgress(
    String id,
    String studentId,
  ) async {
    final response = await _api.list(
      '/micro/progress-logs',
      params: {
        'micro_school_id': id,
        'student_id': studentId,
      },
    );
    return MicroStudentProgress(
      studentId: studentId,
      studentName: studentId,
      milestonesCompleted: response.data.length,
      progressRate: response.data.isEmpty ? 0 : 100,
      series: response.data
          .map(
            (item) => MicroMetricPoint(
              label: item['date']?.toString() ?? '',
              value: 1,
            ),
          )
          .toList(),
    );
  }

  @override
  Future<Map<String, dynamic>> createGroup(
    String id,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post(
      '/micro/groups',
      body: {
        'micro_school_id': id,
        'name': payload['name'],
        'age_range_min': payload['age_range_min'] ?? 2,
        'age_range_max': payload['age_range_max'] ?? 6,
      },
    );
    return response.data;
  }

  @override
  Future<List<Map<String, dynamic>>> getGroups(String id) async {
    final response = await _api.list('/micro/schools/$id/groups');
    return response.data;
  }

  @override
  Future<MicroEnrollment> createEnrollment(Map<String, dynamic> payload) async {
    final response = await _api.post('/micro/enrollments', body: payload);
    return MicroEnrollment.fromJson(response.data);
  }

  @override
  Future<List<MicroEnrollment>> listEnrollments({
    Map<String, dynamic>? params,
  }) async {
    final response = await _api.list('/micro/enrollments', params: params);
    return response.data.map(MicroEnrollment.fromJson).toList();
  }

  @override
  Future<MicroPayment> createTopLevelPayment(
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post('/micro/payments', body: payload);
    return MicroPayment.fromJson(response.data);
  }

  @override
  Future<List<MicroPayment>> listPayments({
    Map<String, dynamic>? params,
  }) async {
    final response = await _api.list('/micro/payments', params: params);
    return response.data.map(MicroPayment.fromJson).toList();
  }

  @override
  Future<Map<String, dynamic>> getPaymentAnalytics({
    Map<String, dynamic>? params,
  }) async {
    final response =
        await _api.get('/micro/payments/analytics', params: params);
    return response.data;
  }

  @override
  Future<MicroResource> createTopLevelResource(
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post('/micro/resources', body: payload);
    return MicroResource.fromJson(response.data);
  }

  @override
  Future<List<MicroResource>> listTopLevelResources({
    Map<String, dynamic>? params,
  }) async {
    final response = await _api.list('/micro/resources', params: params);
    return response.data.map(MicroResource.fromJson).toList();
  }

  @override
  Future<Map<String, dynamic>> createProgressLog(
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post('/micro/progress-logs', body: payload);
    return response.data;
  }

  @override
  Future<List<Map<String, dynamic>>> listProgressLogs({
    Map<String, dynamic>? params,
  }) async {
    final response = await _api.list('/micro/progress-logs', params: params);
    return response.data;
  }
}
