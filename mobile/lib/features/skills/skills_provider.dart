import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/skills.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';

final academicYearIdProvider = Provider<String>((ref) {
  return DateTime.now().year.toString();
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
