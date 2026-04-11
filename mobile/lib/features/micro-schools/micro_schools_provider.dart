import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/micro_school.dart';

final microSchoolsProvider = FutureProvider<List<MicroSchool>>((ref) async {
  return ref.read(microSchoolRepositoryProvider).listMicroSchools();
});

final microSchoolDetailProvider =
    FutureProvider.family<MicroSchoolDetailBundle, String>(
        (ref, schoolId) async {
  final repository = ref.read(microSchoolRepositoryProvider);
  final results = await Future.wait<dynamic>([
    repository.getMicroSchoolDetail(schoolId),
    repository.getEnrollments(schoolId),
    repository.getResources(schoolId),
    repository.getPayments(schoolId),
    repository.getProgress(schoolId),
  ]);

  return MicroSchoolDetailBundle(
    school: results[0] as MicroSchool,
    enrollments: results[1] as List<MicroEnrollment>,
    resources: results[2] as List<MicroResource>,
    payments: results[3] as List<MicroPayment>,
    progress: results[4] as MicroProgressOverview,
  );
});

class MicroSchoolActionNotifier extends AsyncNotifier<void> {
  @override
  Future<void> build() async {}

  Future<void> enroll({
    required String schoolId,
    required String studentName,
  }) async {
    state = const AsyncLoading();
    state = await AsyncValue.guard(() async {
      await ref.read(microSchoolRepositoryProvider).enrollStudent(
        schoolId,
        {'student_name': studentName},
      );
      ref.invalidate(microSchoolDetailProvider(schoolId));
      ref.invalidate(microSchoolsProvider);
    });
  }
}

final microSchoolActionProvider =
    AsyncNotifierProvider<MicroSchoolActionNotifier, void>(
  MicroSchoolActionNotifier.new,
);
