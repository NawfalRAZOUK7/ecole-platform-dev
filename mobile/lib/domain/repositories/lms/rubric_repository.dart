import 'package:ecole_platform/domain/entities/lms/rubric.dart';

abstract class RubricRepository {
  Future<List<Rubric>> listRubrics();

  Future<Rubric> getRubric(String id);

  Future<Rubric> createRubric({
    required String title,
    String? description,
    String? subject,
    required List<RubricCriterion> criteria,
  });

  Future<Rubric> updateRubric({
    required String id,
    required String title,
    String? description,
    String? subject,
    required List<RubricCriterion> criteria,
  });

  Future<Rubric> duplicateRubric(String id);

  Future<RubricGradeResult> gradeRubric({
    required String rubricId,
    String? assignmentId,
    required List<RubricGradeEntry> entries,
  });

  Future<RubricResultsResponse> getRubricResults(String rubricId);
}
