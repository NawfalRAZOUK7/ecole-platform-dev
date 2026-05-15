/// Teacher domain entities — classes, assignments, submissions, attendance.
///
/// Reference: Phase 5B (from 4B)

class ClassInfo {
  final String id;
  final String code;
  final String name;
  final int studentCount;
  final int courseCount;

  const ClassInfo({
    required this.id,
    required this.code,
    required this.name,
    required this.studentCount,
    required this.courseCount,
  });
}

class StudentInfo {
  final String id;
  final String fullName;
  final String email;
  final String enrollmentStatus;

  const StudentInfo({
    required this.id,
    required this.fullName,
    required this.email,
    required this.enrollmentStatus,
  });
}

class Course {
  final String id;
  final String classId;
  final String title;
  final String? description;
  final String status;

  const Course({
    required this.id,
    required this.classId,
    required this.title,
    this.description,
    required this.status,
  });
}

class Assignment {
  final String id;
  final String courseId;
  final String title;
  final String? description;
  final String? dueAt;
  final int totalPoints;

  const Assignment({
    required this.id,
    required this.courseId,
    required this.title,
    this.description,
    this.dueAt,
    required this.totalPoints,
  });
}

class Submission {
  final String id;
  final String assignmentId;
  final String? assignmentTitle;
  final int? assignmentTotalPoints;
  final String studentId;
  final String? studentName;
  final String status;
  final String? submittedAt;
  final double? score;
  final String? feedbackText;
  final String? publishedAt;

  const Submission({
    required this.id,
    required this.assignmentId,
    this.assignmentTitle,
    this.assignmentTotalPoints,
    required this.studentId,
    this.studentName,
    required this.status,
    this.submittedAt,
    this.score,
    this.feedbackText,
    this.publishedAt,
  });
}

class Period {
  final String id;
  final String name;

  const Period({required this.id, required this.name});
}

class AttendanceRecord {
  String studentId;
  String status;
  String? absenceReason;

  AttendanceRecord({
    required this.studentId,
    this.status = 'present',
    this.absenceReason,
  });
}
