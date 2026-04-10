import 'package:ecole_platform/domain/entities/gradebook.dart';

abstract class GradebookRepository {
  Future<GradebookGrid> getClassGradebook(String classId);

  Future<StudentGradeDetail> getStudentGrades(String studentId);

  Future<void> updateGrades(BulkGradeUpdate update);

  Future<WeightedSummary> getWeightedSummary(String classId, {String? periodId});

  Future<String?> exportGrades(String classId, {String format = 'csv'});

  Future<List<String>> getCategories(String classId);

  Future<WeightedSummary> computeGrades(String classId, {String? periodId});

  Future<GradeTranscript> getTranscript(String studentId);
}
