/// Teacher repository implementation — data layer.
///
/// Reference: Phase 5B (from 4B)

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';
import 'package:ecole_platform/domain/repositories/teacher_repository.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';

class TeacherRepositoryImpl implements TeacherRepository {
  final ApiClient _api;

  TeacherRepositoryImpl({required ApiClient api}) : _api = api;

  @override
  Future<List<ClassInfo>> getClasses() async {
    final resp = await _api.list('/teacher/classes');
    return resp.data.map(classInfoFromJson).toList();
  }

  @override
  Future<List<StudentInfo>> getClassStudents(String classId) async {
    final resp = await _api.list('/teacher/classes/$classId/students');
    return resp.data.map(studentInfoFromJson).toList();
  }

  @override
  Future<List<Course>> getCourses({String? classId}) async {
    final params = <String, dynamic>{};
    if (classId != null) params['class_id'] = classId;
    final resp = await _api.list('/courses', params: params);
    return resp.data.map(courseFromJson).toList();
  }

  @override
  Future<Course> createCourse({
    required String classId,
    required String title,
    String? description,
    String status = 'draft',
  }) async {
    final resp = await _api.post('/courses', body: {
      'class_id': classId,
      'title': title,
      if (description != null) 'description': description,
      'status': status,
    });
    return courseFromJson(resp.data);
  }

  @override
  Future<PaginatedList<Assignment>> getAssignments({
    String? cursor,
    String? courseId,
  }) async {
    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;
    if (courseId != null) params['course_id'] = courseId;
    final resp = await _api.list('/assignments', params: params);
    return PaginatedList(
      items: resp.data.map(assignmentFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }

  @override
  Future<Assignment> createAssignment({
    required String courseId,
    required String title,
    String? description,
    String? dueAt,
    int totalPoints = 20,
  }) async {
    final resp = await _api.post('/assignments', body: {
      'course_id': courseId,
      'title': title,
      if (description != null) 'description': description,
      if (dueAt != null) 'due_at': dueAt,
      'total_points': totalPoints,
    });
    return assignmentFromJson(resp.data);
  }

  @override
  Future<PaginatedList<Submission>> getSubmissions({
    String? cursor,
    String? status,
  }) async {
    final params = <String, dynamic>{};
    if (cursor != null) params['cursor'] = cursor;
    if (status != null) params['status'] = status;
    final resp = await _api.list('/teacher/submissions', params: params);
    return PaginatedList(
      items: resp.data.map(submissionFromJson).toList(),
      nextCursor: resp.nextCursor,
      hasMore: resp.hasMore,
    );
  }

  @override
  Future<void> gradeSubmission(
    String submissionId, {
    required double score,
    String? feedbackText,
    bool publish = true,
  }) async {
    await _api.post('/submissions/$submissionId/grade', body: {
      'score': score,
      if (feedbackText != null) 'feedback_text': feedbackText,
      'publish': publish,
    });
  }

  @override
  Future<List<Period>> getPeriods() async {
    final resp = await _api.list('/teacher/periods');
    return resp.data.map(periodFromJson).toList();
  }

  @override
  Future<void> createAttendanceSession({
    required String classId,
    required String periodId,
    required String sessionDate,
    required String slot,
    required List<AttendanceRecord> records,
  }) async {
    await _api.post('/attendance/sessions', body: {
      'class_id': classId,
      'period_id': periodId,
      'session_date': sessionDate,
      'slot': slot,
      'records': records
          .map((r) => {
                'student_id': r.studentId,
                'status': r.status,
                if (r.absenceReason != null) 'absence_reason': r.absenceReason,
              })
          .toList(),
    });
  }
}
