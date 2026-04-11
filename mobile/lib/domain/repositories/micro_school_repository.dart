import 'package:ecole_platform/domain/entities/micro_school.dart';

abstract class MicroSchoolRepository {
  Future<List<MicroSchool>> listMicroSchools({
    Map<String, dynamic>? params,
  });

  Future<MicroSchool> createMicroSchool(Map<String, dynamic> payload);

  Future<MicroSchool> getMicroSchoolDetail(String id);

  Future<MicroSchool> updateMicroSchool(
      String id, Map<String, dynamic> payload);

  Future<void> deleteMicroSchool(String id);

  Future<List<MicroEnrollment>> getEnrollments(String id);

  Future<MicroEnrollment> enrollStudent(
      String id, Map<String, dynamic> payload);

  Future<void> unenrollStudent(String id, String enrollmentId);

  Future<List<MicroPayment>> getPayments(String id);

  Future<MicroPayment> createPayment(String id, Map<String, dynamic> payload);

  Future<List<MicroResource>> getResources(String id);

  Future<MicroResource> addResource(String id, Map<String, dynamic> payload);

  Future<MicroProgressOverview> getProgress(String id);

  Future<MicroStudentProgress> getStudentProgress(String id, String studentId);

  Future<Map<String, dynamic>> createGroup(
      String id, Map<String, dynamic> payload);

  Future<List<Map<String, dynamic>>> getGroups(String id);

  Future<MicroEnrollment> createEnrollment(Map<String, dynamic> payload);

  Future<List<MicroEnrollment>> listEnrollments({
    Map<String, dynamic>? params,
  });

  Future<MicroPayment> createTopLevelPayment(Map<String, dynamic> payload);

  Future<List<MicroPayment>> listPayments({
    Map<String, dynamic>? params,
  });

  Future<Map<String, dynamic>> getPaymentAnalytics({
    Map<String, dynamic>? params,
  });

  Future<MicroResource> createTopLevelResource(Map<String, dynamic> payload);

  Future<List<MicroResource>> listTopLevelResources({
    Map<String, dynamic>? params,
  });

  Future<Map<String, dynamic>> createProgressLog(Map<String, dynamic> payload);

  Future<List<Map<String, dynamic>>> listProgressLogs({
    Map<String, dynamic>? params,
  });
}
