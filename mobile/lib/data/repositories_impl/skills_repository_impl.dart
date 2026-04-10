import 'dart:io';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/domain/entities/skills.dart';
import 'package:ecole_platform/domain/repositories/skills_repository.dart';
import 'package:path_provider/path_provider.dart';

class SkillsRepositoryImpl implements SkillsRepository {
  final ApiClient _api;

  SkillsRepositoryImpl({required ApiClient api}) : _api = api;

  @override
  Future<List<SkillDimension>> listDimensions({bool? isActive}) async {
    final response = await _api.list('/skills/dimensions', params: {
      if (isActive != null) 'is_active': '$isActive',
    });
    return response.data.map(SkillDimension.fromJson).toList();
  }

  @override
  Future<SkillDimension> createDimension(Map<String, dynamic> payload) async {
    final response = await _api.post('/skills/dimensions', body: payload);
    return SkillDimension.fromJson(response.data);
  }

  @override
  Future<List<SkillMilestone>> listMilestones({
    String? dimensionId,
    bool? isActive,
  }) async {
    final response = await _api.list('/skills/milestones', params: {
      if (dimensionId != null) 'dimension_id': dimensionId,
      if (isActive != null) 'is_active': '$isActive',
    });
    return response.data.map(SkillMilestone.fromJson).toList();
  }

  @override
  Future<SkillMilestone> createMilestone(Map<String, dynamic> payload) async {
    final response = await _api.post('/skills/milestones', body: payload);
    return SkillMilestone.fromJson(response.data);
  }

  @override
  Future<List<SkillProgressItem>> getStudentProgress(
    String studentId, {
    required String academicYearId,
  }) async {
    final response = await _api.list(
      '/skills/progress/student/$studentId',
      params: {'academic_year_id': academicYearId},
    );
    return response.data.map(SkillProgressItem.fromJson).toList();
  }

  @override
  Future<SkillEvaluation> evaluateStudent(
    String studentId, {
    required String academicYearId,
  }) async {
    final response = await _api.post(
      '/skills/evaluate/$studentId?academic_year_id=$academicYearId',
    );
    return SkillEvaluation.fromJson(response.data);
  }

  @override
  Future<SkillPassport> getPassport(
    String studentId, {
    required String academicYearId,
  }) async {
    final response = await _api.get(
      '/skills/passport/$studentId',
      params: {'academic_year_id': academicYearId},
    );
    return SkillPassport.fromJson(response.data);
  }

  @override
  Future<SkillPassport> generatePassport(
    String studentId, {
    required String academicYearId,
  }) async {
    final response = await _api.post(
      '/skills/passport/$studentId/generate?academic_year_id=$academicYearId',
    );
    return SkillPassport.fromJson(response.data);
  }

  @override
  Future<File> downloadPassport(
    String studentId, {
    required String academicYearId,
  }) async {
    final directory = await getTemporaryDirectory();
    final path = '${directory.path}/skills-passport-$studentId.pdf';
    return _api.download(
      '/skills/passport/$studentId/download?academic_year_id=$academicYearId',
      savePath: path,
    );
  }

  @override
  Future<SkillClassAnalytics> getClassAnalytics(
    String classId, {
    required String academicYearId,
  }) async {
    final response = await _api.get(
      '/skills/analytics/class/$classId',
      params: {'academic_year_id': academicYearId},
    );
    return SkillClassAnalytics.fromJson(response.data);
  }

  @override
  Future<SkillSchoolAnalytics> getSchoolAnalytics({
    required String academicYearId,
  }) async {
    final response = await _api.get(
      '/skills/analytics/school',
      params: {'academic_year_id': academicYearId},
    );
    return SkillSchoolAnalytics.fromJson(response.data);
  }

  @override
  Future<List<SkillLeaderboardEntry>> getLeaderboard(
    String classId, {
    required String academicYearId,
    int limit = 10,
  }) async {
    final response = await _api.list(
      '/skills/leaderboard/$classId',
      params: {
        'academic_year_id': academicYearId,
        'limit': limit,
      },
    );
    return response.data.map(SkillLeaderboardEntry.fromJson).toList();
  }
}
