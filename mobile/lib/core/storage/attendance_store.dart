import 'package:ecole_platform/core/storage/cache_store.dart';

class AttendanceStore {
  final CacheStore _cache;

  const AttendanceStore({
    required CacheStore cache,
  }) : _cache = cache;

  Future<List<Map<String, dynamic>>?> readClassAttendance(
    String classId,
    String date,
  ) {
    return _cache.get(_classAttendanceKey(classId, date));
  }

  Future<void> writeClassAttendance(
    String classId,
    String date,
    List<Map<String, dynamic>> records,
  ) {
    return _cache.put(
      _classAttendanceKey(classId, date),
      records,
      CacheTtl.attendance,
    );
  }

  Future<List<Map<String, dynamic>>?> readStudentHistory(String studentId) {
    return _cache.get(_studentHistoryKey(studentId));
  }

  Future<void> writeStudentHistory(
    String studentId,
    List<Map<String, dynamic>> records,
  ) {
    return _cache.put(
      _studentHistoryKey(studentId),
      records,
      CacheTtl.attendance,
    );
  }

  Future<Map<String, dynamic>?> readClassStats(String classId) async {
    final cached = await _cache.get(_classStatsKey(classId));
    return cached?.firstOrNull;
  }

  Future<void> writeClassStats(String classId, Map<String, dynamic> stats) {
    return _cache.put(
      _classStatsKey(classId),
      [stats],
      CacheTtl.attendance,
    );
  }

  Future<List<Map<String, dynamic>>?> readClassTrends(
    String classId,
    String from,
    String to,
  ) {
    return _cache.get(_classTrendsKey(classId, from, to));
  }

  Future<void> writeClassTrends(
    String classId,
    String from,
    String to,
    List<Map<String, dynamic>> trends,
  ) {
    return _cache.put(
      _classTrendsKey(classId, from, to),
      trends,
      CacheTtl.attendance,
    );
  }

  Future<List<Map<String, dynamic>>?> readAlerts(String schoolId) {
    return _cache.get(_alertsKey(schoolId));
  }

  Future<void> writeAlerts(
    String schoolId,
    List<Map<String, dynamic>> alerts,
  ) {
    return _cache.put(_alertsKey(schoolId), alerts, CacheTtl.attendance);
  }

  Future<void> invalidateClass(String classId) {
    return _cache.invalidatePrefix('attendance:class:$classId');
  }

  Future<void> invalidateStudent(String studentId) {
    return _cache.invalidate(_studentHistoryKey(studentId));
  }

  String _classAttendanceKey(String classId, String date) {
    return 'attendance:class:$classId:$date';
  }

  String _studentHistoryKey(String studentId) {
    return 'attendance:history:$studentId';
  }

  String _classStatsKey(String classId) {
    return 'attendance:stats:$classId';
  }

  String _classTrendsKey(String classId, String from, String to) {
    return 'attendance:trends:$classId:$from:$to';
  }

  String _alertsKey(String schoolId) {
    return 'attendance:alerts:$schoolId';
  }
}
