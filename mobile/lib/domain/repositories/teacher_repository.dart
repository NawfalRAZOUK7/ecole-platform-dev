/// Teacher repository interface — domain layer contract.
///
/// Reference: Phase 5B (from 4B)
import '../entities/teacher.dart';
import 'feed_repository.dart';

abstract class TeacherRepository {
  Future<List<ClassInfo>> getClasses();
  Future<List<StudentInfo>> getClassStudents(String classId);

  Future<List<Course>> getCourses({String? classId});
  Future<Course> createCourse({
    required String classId,
    required String title,
    String? description,
    String status = 'draft',
  });

  Future<PaginatedList<Assignment>> getAssignments({
    String? cursor,
    String? courseId,
  });

  Future<Assignment> createAssignment({
    required String courseId,
    required String title,
    String? description,
    String? dueAt,
    int totalPoints = 20,
  });

  Future<PaginatedList<Submission>> getSubmissions({
    String? cursor,
    String? status,
  });

  Future<void> gradeSubmission(
    String submissionId, {
    required double score,
    String? feedbackText,
    bool publish = true,
  });

  Future<List<Period>> getPeriods();

  Future<void> createAttendanceSession({
    required String classId,
    required String periodId,
    required String sessionDate,
    required String slot,
    required List<AttendanceRecord> records,
  });
}
