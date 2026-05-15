import 'package:ecole_platform/domain/entities/admin/compliance.dart';

abstract class ComplianceRepository {
  Future<List<MenCurriculum>> listCurricula({Map<String, dynamic>? params});

  Future<MenCurriculum> createCurriculum(Map<String, dynamic> payload);

  Future<List<MenObjective>> listObjectives(
    String curriculumId, {
    int? trimester,
  });

  Future<MenObjective> createObjective(
    String curriculumId,
    Map<String, dynamic> payload,
  );

  Future<CurriculumMapping> createMapping(Map<String, dynamic> payload);

  Future<List<CurriculumMapping>> listMappings({Map<String, dynamic>? params});

  Future<void> deleteMapping(String mappingId);

  Future<ComplianceDashboardData> getDashboard({
    required String academicYearId,
    String? level,
    String? grade,
    String? subject,
  });

  Future<ComplianceReport> generateReport(Map<String, dynamic> payload);

  Future<List<ComplianceReport>> listReports({Map<String, dynamic>? params});

  Future<ComplianceReport> getReport(String reportId);

  Future<Map<String, dynamic>> downloadReport(String reportId);
}
