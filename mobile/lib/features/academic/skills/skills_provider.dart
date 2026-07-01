import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/academic/skills.dart';
import 'package:ecole_platform/domain/entities/lms/teacher.dart';

// TODO: replace with GET /academic-years/current once that endpoint exists
const _kDevAcademicYearId = '20000000-0000-4000-8000-000000000001';

final academicYearIdProvider = Provider<String>((ref) {
  return _kDevAcademicYearId;
});

final skillsClassesProvider = FutureProvider<List<ClassInfo>>((ref) async {
  return ref.read(teacherRepositoryProvider).getClasses();
});

final skillsStudentsProvider =
    FutureProvider.family<List<StudentInfo>, String>((ref, classId) async {
  return ref.read(teacherRepositoryProvider).getClassStudents(classId);
});

final skillsOverviewProvider =
    FutureProvider<SkillSchoolAnalytics>((ref) async {
  return ref.read(skillsRepositoryProvider).getSchoolAnalytics(
        academicYearId: ref.read(academicYearIdProvider),
      );
});

final skillPassportProvider =
    FutureProvider.family<SkillPassport, String>((ref, studentId) async {
  return ref.read(skillsRepositoryProvider).getPassport(
        studentId,
        academicYearId: ref.read(academicYearIdProvider),
      );
});

final skillProgressProvider =
    FutureProvider.family<List<SkillProgressItem>, String>(
        (ref, studentId) async {
  return ref.read(skillsRepositoryProvider).getStudentProgress(
        studentId,
        academicYearId: ref.read(academicYearIdProvider),
      );
});

final skillAnalyticsProvider =
    FutureProvider.family<SkillAnalyticsBundle, String>((ref, classId) async {
  final repository = ref.read(skillsRepositoryProvider);
  final academicYearId = ref.read(academicYearIdProvider);
  final results = await Future.wait<dynamic>([
    repository.getClassAnalytics(classId, academicYearId: academicYearId),
    repository.getLeaderboard(
      classId,
      academicYearId: academicYearId,
    ),
  ]);

  return SkillAnalyticsBundle(
    analytics: results[0] as SkillClassAnalytics,
    leaderboard: results[1] as List<SkillLeaderboardEntry>,
  );
});
