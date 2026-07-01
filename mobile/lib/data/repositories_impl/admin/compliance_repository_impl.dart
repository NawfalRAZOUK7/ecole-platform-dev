import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/domain/entities/admin/compliance.dart';
import 'package:ecole_platform/domain/repositories/admin/compliance_repository.dart';

class ComplianceRepositoryImpl implements ComplianceRepository {
  final ApiClient _api;

  ComplianceRepositoryImpl({required ApiClient api}) : _api = api;

  @override
  Future<List<MenCurriculum>> listCurricula({
    Map<String, dynamic>? params,
  }) async {
    final response = await _api.list('/compliance/curricula', params: params);
    return response.data.map(MenCurriculum.fromJson).toList();
  }

  @override
  Future<MenCurriculum> createCurriculum(Map<String, dynamic> payload) async {
    final response = await _api.post('/compliance/curricula', body: payload);
    return MenCurriculum.fromJson(response.data);
  }

  @override
  Future<List<MenObjective>> listObjectives(
    String curriculumId, {
    int? trimester,
  }) async {
    final response = await _api.list(
      '/compliance/curricula/$curriculumId/objectives',
      params: {
        if (trimester != null) 'trimester': trimester,
      },
    );
    return response.data.map(MenObjective.fromJson).toList();
  }

  @override
  Future<MenObjective> createObjective(
    String curriculumId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post(
      '/compliance/curricula/$curriculumId/objectives',
      body: payload,
    );
    return MenObjective.fromJson(response.data);
  }

  @override
  Future<CurriculumMapping> createMapping(Map<String, dynamic> payload) async {
    final response = await _api.post('/compliance/mappings', body: payload);
    return CurriculumMapping.fromJson(response.data);
  }

  @override
  Future<List<CurriculumMapping>> listMappings({
    Map<String, dynamic>? params,
  }) async {
    final response = await _api.list('/compliance/mappings', params: params);
    return response.data.map(CurriculumMapping.fromJson).toList();
  }

  @override
  Future<void> deleteMapping(String mappingId) async {
    await _api.delete('/compliance/mappings/$mappingId');
  }

  @override
  Future<ComplianceDashboardData> getDashboard({
    required String academicYearId,
    String? level,
    String? grade,
    String? subject,
  }) async {
    final response = await _api.get(
      '/compliance/dashboard',
      params: {
        'academic_year_id': academicYearId,
        if (level != null) 'level': level,
        if (grade != null) 'grade': grade,
        if (subject != null) 'subject': subject,
      },
    );
    return ComplianceDashboardData.fromJson(response.data);
  }

  @override
  Future<ComplianceReport> generateReport(Map<String, dynamic> payload) async {
    final response =
        await _api.post('/compliance/reports/generate', body: payload);
    return ComplianceReport.fromJson(response.data);
  }

  @override
  Future<List<ComplianceReport>> listReports({
    Map<String, dynamic>? params,
  }) async {
    final response = await _api.list('/compliance/reports', params: params);
    return response.data.map(ComplianceReport.fromJson).toList();
  }

  @override
  Future<ComplianceReport> getReport(String reportId) async {
    final response = await _api.get('/compliance/reports/$reportId');
    return ComplianceReport.fromJson(response.data);
  }

  @override
  Future<Map<String, dynamic>> downloadReport(String reportId) async {
    final response = await _api.get('/compliance/reports/$reportId/download');
    return response.data;
  }
}
