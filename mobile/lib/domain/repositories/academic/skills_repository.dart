import 'dart:io';

import 'package:ecole_platform/domain/entities/academic/skills.dart';

abstract class SkillsRepository {
  Future<List<SkillDimension>> listDimensions({bool? isActive});

  Future<SkillDimension> createDimension(Map<String, dynamic> payload);

  Future<List<SkillMilestone>> listMilestones({
    String? dimensionId,
    bool? isActive,
  });

  Future<SkillMilestone> createMilestone(Map<String, dynamic> payload);

  Future<List<SkillProgressItem>> getStudentProgress(
    String studentId, {
    required String academicYearId,
  });

  Future<SkillEvaluation> evaluateStudent(
    String studentId, {
    required String academicYearId,
  });

  Future<SkillPassport> getPassport(
    String studentId, {
    required String academicYearId,
  });

  Future<SkillPassport> generatePassport(
    String studentId, {
    required String academicYearId,
  });

  Future<File> downloadPassport(
    String studentId, {
    required String academicYearId,
  });

  Future<SkillClassAnalytics> getClassAnalytics(
    String classId, {
    required String academicYearId,
  });

  Future<SkillSchoolAnalytics> getSchoolAnalytics({
    required String academicYearId,
  });

  Future<List<SkillLeaderboardEntry>> getLeaderboard(
    String classId, {
    required String academicYearId,
    int limit = 10,
  });
}
