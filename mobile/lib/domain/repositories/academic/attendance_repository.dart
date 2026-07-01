import 'package:ecole_platform/domain/entities/academic/attendance.dart';

abstract class AttendanceRepository {
  Future<List<AttendanceEntry>> getClassAttendance(
    String classId, {
    required String date,
  });

  Future<void> markAttendance({
    required String classId,
    required String date,
    required List<AttendanceBulkRecord> records,
  });

  Future<AttendanceJustification> submitJustification({
    required String recordId,
    required String reason,
    String? attachmentName,
  });

  Future<List<AttendanceTrendPoint>> getAttendanceTrends(
    String classId, {
    required String from,
    required String to,
  });

  Future<List<AttendanceAlertItem>> getAttendanceAlerts({
    required String schoolId,
  });

  Future<List<AttendanceEntry>> getStudentHistory(String studentId);

  Future<AttendanceClassStats> getClassStats(
    String classId, {
    bool export = false,
  });

  Future<AttendanceExportResult> exportAttendance(
    String classId, {
    required String format,
  });

  Future<AttendanceJustification> reviewJustification({
    required String justificationId,
    required String status,
    String? reviewComment,
  });

  Future<List<AttendanceThresholdResult>> checkThresholds();
}
