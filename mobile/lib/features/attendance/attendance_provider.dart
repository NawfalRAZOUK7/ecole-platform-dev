import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/attendance.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';

class AttendanceAnalyticsBundle {
  final AttendanceClassStats stats;
  final List<AttendanceTrendPoint> trends;
  final List<AttendanceAlertItem> alerts;

  const AttendanceAnalyticsBundle({
    required this.stats,
    required this.trends,
    required this.alerts,
  });
}

final attendanceClassesProvider = FutureProvider<List<ClassInfo>>((ref) async {
  return ref.read(teacherRepositoryProvider).getClasses();
});

final attendanceStudentsProvider =
    FutureProvider.family<List<StudentInfo>, String>((ref, classId) async {
  return ref.read(teacherRepositoryProvider).getClassStudents(classId);
});

final attendanceHistoryProvider =
    FutureProvider.family<List<AttendanceEntry>, String>((ref, studentId) async {
  return ref.read(attendanceRepositoryProvider).getStudentHistory(studentId);
});

final attendanceAnalyticsProvider =
    FutureProvider.family<AttendanceAnalyticsBundle, String>((ref, classId) async {
  final repository = ref.read(attendanceRepositoryProvider);
  final authState = ref.read(authProvider);
  final now = DateTime.now();
  final formatter = DateFormat('yyyy-MM-dd');
  final from = formatter.format(now.subtract(const Duration(days: 35)));
  final to = formatter.format(now);

  final results = await Future.wait<dynamic>([
    repository.getClassStats(classId),
    repository.getAttendanceTrends(classId, from: from, to: to),
    repository.getAttendanceAlerts(
      schoolId: authState.user?.schoolId ?? '',
    ),
  ]);

  return AttendanceAnalyticsBundle(
    stats: results[0] as AttendanceClassStats,
    trends: results[1] as List<AttendanceTrendPoint>,
    alerts: results[2] as List<AttendanceAlertItem>,
  );
});
