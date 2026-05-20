import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/academic/gradebook.dart';
import 'package:ecole_platform/domain/entities/lms/teacher.dart';

final gradebookClassesProvider = FutureProvider<List<ClassInfo>>((ref) async {
  return ref.read(teacherRepositoryProvider).getClasses();
});

class GradebookNotifier extends FamilyAsyncNotifier<GradebookGrid, String> {
  @override
  Future<GradebookGrid> build(String arg) async {
    return ref.read(gradebookRepositoryProvider).getClassGradebook(arg);
  }

  Future<void> refresh() async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(gradebookRepositoryProvider).getClassGradebook(arg),
    );
  }
}

final gradebookProvider =
    AsyncNotifierProvider.family<GradebookNotifier, GradebookGrid, String>(
  GradebookNotifier.new,
);

final studentGradeDetailProvider =
    FutureProvider.family<StudentGradeDetail, String>((ref, studentId) async {
  return ref.read(gradebookRepositoryProvider).getStudentGrades(studentId);
});

final gradeTranscriptProvider =
    FutureProvider.family<GradeTranscript, String>((ref, studentId) async {
  return ref.read(gradebookRepositoryProvider).getTranscript(studentId);
});

class GradeUpdateNotifier extends AsyncNotifier<void> {
  @override
  Future<void> build() async {}

  Future<void> save(BulkGradeUpdate update) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => ref.read(gradebookRepositoryProvider).updateGrades(update),
    );
    ref.invalidate(gradebookProvider(update.classId));
  }
}

final gradeUpdateProvider =
    AsyncNotifierProvider<GradeUpdateNotifier, void>(GradeUpdateNotifier.new);
