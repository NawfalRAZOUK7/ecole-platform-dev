import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/lms/rubric.dart';

final rubricsProvider = FutureProvider<List<Rubric>>((ref) async {
  return ref.read(rubricRepositoryProvider).listRubrics();
});

final rubricProvider = FutureProvider.family<Rubric, String>((ref, id) async {
  return ref.read(rubricRepositoryProvider).getRubric(id);
});

final rubricResultsProvider =
    FutureProvider.family<RubricResultsResponse, String>((ref, id) async {
  return ref.read(rubricRepositoryProvider).getRubricResults(id);
});
