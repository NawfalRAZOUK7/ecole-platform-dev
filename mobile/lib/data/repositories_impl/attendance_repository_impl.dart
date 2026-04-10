import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/local_store/attendance_store.dart';
import 'package:ecole_platform/domain/entities/attendance.dart';
import 'package:ecole_platform/domain/repositories/attendance_repository.dart';

class AttendanceRepositoryImpl implements AttendanceRepository {
  final ApiClient _api;
  final AttendanceStore _store;

  AttendanceRepositoryImpl({
    required ApiClient api,
    required AttendanceStore store,
  })  : _api = api,
        _store = store;

  @override
  Future<List<AttendanceEntry>> getClassAttendance(
    String classId, {
    required String date,
  }) async {
    final cached = await _store.readClassAttendance(classId, date);
    if (cached != null) {
      return cached.map(AttendanceEntry.fromJson).toList();
    }

    final response = await _api.list(
      '/attendance/class/$classId',
      params: {'date': date},
    );
    await _store.writeClassAttendance(classId, date, response.data);
    return response.data.map(AttendanceEntry.fromJson).toList();
  }

  @override
  Future<void> markAttendance({
    required String classId,
    required String date,
    required List<AttendanceBulkRecord> records,
  }) async {
    await _api.post('/attendance/class/$classId', body: {
      'date': date,
      'records': records.map((record) => record.toJson()).toList(),
    });
    await _store.invalidateClass(classId);
  }

  @override
  Future<AttendanceJustification> submitJustification({
    required String recordId,
    required String reason,
    String? attachmentName,
  }) async {
    final response = await _api.post('/attendance/justifications', body: {
      'attendance_record_id': recordId,
      'reason': attachmentName == null
          ? reason
          : '$reason\n\nAttachment: $attachmentName',
    });
    return AttendanceJustification.fromJson(response.data);
  }

  @override
  Future<List<AttendanceTrendPoint>> getAttendanceTrends(
    String classId, {
    required String from,
    required String to,
  }) async {
    final cached = await _store.readClassTrends(classId, from, to);
    if (cached != null) {
      return cached.map(AttendanceTrendPoint.fromJson).toList();
    }

    final response = await _api.list(
      '/analytics/attendance/trends/$classId',
      params: {
        'from': from,
        'to': to,
      },
    );
    await _store.writeClassTrends(classId, from, to, response.data);
    return response.data.map(AttendanceTrendPoint.fromJson).toList();
  }

  @override
  Future<List<AttendanceAlertItem>> getAttendanceAlerts({
    required String schoolId,
  }) async {
    final cached = await _store.readAlerts(schoolId);
    if (cached != null) {
      return cached.map(AttendanceAlertItem.fromJson).toList();
    }

    final response = await _api.list(
      '/analytics/attendance/alerts',
      params: {'school_id': schoolId},
    );
    await _store.writeAlerts(schoolId, response.data);
    return response.data.map(AttendanceAlertItem.fromJson).toList();
  }

  @override
  Future<List<AttendanceEntry>> getStudentHistory(String studentId) async {
    final cached = await _store.readStudentHistory(studentId);
    if (cached != null) {
      return cached.map(AttendanceEntry.fromJson).toList();
    }

    final response = await _api.list('/analytics/attendance/student/$studentId');
    await _store.writeStudentHistory(studentId, response.data);
    return response.data.map(AttendanceEntry.fromJson).toList();
  }

  @override
  Future<AttendanceClassStats> getClassStats(
    String classId, {
    bool export = false,
  }) async {
    if (!export) {
      final cached = await _store.readClassStats(classId);
      if (cached != null) {
        return AttendanceClassStats.fromJson(cached);
      }
    }

    final response = await _api.get(
      '/analytics/attendance/class/$classId',
      params: export ? {'export': 'true'} : null,
    );
    if (!export) {
      await _store.writeClassStats(classId, response.data);
    }
    return AttendanceClassStats.fromJson(response.data);
  }

  @override
  Future<AttendanceExportResult> exportAttendance(
    String classId, {
    required String format,
  }) async {
    await getClassStats(classId, export: true);
    final normalizedFormat = format == 'pdf' ? 'xlsx' : format;
    return AttendanceExportResult(
      downloadUrl: '/api/v1/export/$normalizedFormat?entity=attendance&class_id=$classId',
      fileName: 'attendance-$classId.$normalizedFormat',
    );
  }

  @override
  Future<AttendanceJustification> reviewJustification({
    required String justificationId,
    required String status,
    String? reviewComment,
  }) async {
    final response = await _api.post(
      '/attendance/justifications/$justificationId/review',
      body: {
        'status': status,
        if (reviewComment != null) 'review_comment': reviewComment,
      },
    );
    return AttendanceJustification.fromJson(response.data);
  }

  @override
  Future<List<AttendanceThresholdResult>> checkThresholds() async {
    final response = await _api.postList(
      '/analytics/attendance/check-thresholds',
      body: const {},
    );
    return response.data.map(AttendanceThresholdResult.fromJson).toList();
  }
}
