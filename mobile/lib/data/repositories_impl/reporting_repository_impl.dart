import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/dto/mappers.dart';
import 'package:ecole_platform/data/local_store/reports_store.dart';
import 'package:ecole_platform/domain/entities/reporting.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';
import 'package:ecole_platform/domain/repositories/reporting_repository.dart';

class ReportingRepositoryImpl implements ReportingRepository {
  final ApiClient _api;
  final ReportsStore _reportsStore;

  ReportingRepositoryImpl({
    required ApiClient api,
    required ReportsStore reportsStore,
  })  : _api = api,
        _reportsStore = reportsStore;

  @override
  Future<ReportOptions> getReportOptions({
    String? type,
    String? classId,
  }) async {
    final response = await _api.get(
      '/reports/options',
      params: {
        if (type != null && type.isNotEmpty) 'type': type,
        if (classId != null && classId.isNotEmpty) 'class_id': classId,
      },
    );

    return ReportOptions(
      classes: (response.data['classes'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>()
          .map((item) => reportOptionFromJson(
                item,
                primaryKey: 'code',
                secondaryKeys: const ['name'],
              ))
          .toList(),
      periods: (response.data['periods'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>()
          .map(reportOptionFromJson)
          .toList(),
      students: (response.data['students'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>()
          .map((item) => reportOptionFromJson(
                item,
                primaryKey: 'full_name',
                secondaryKeys: const ['email'],
              ))
          .toList(),
      parents: (response.data['parents'] as List<dynamic>? ?? const [])
          .cast<Map<String, dynamic>>()
          .map((item) => reportOptionFromJson(
                item,
                primaryKey: 'full_name',
                secondaryKeys: const ['email'],
              ))
          .toList(),
    );
  }

  @override
  Future<PaginatedList<ReportJob>> getReportJobs({
    String? cursor,
    String? type,
    String? status,
  }) async {
    try {
      final response = await _api.list(
        '/reports',
        params: {
          if (cursor != null && cursor.isNotEmpty) 'cursor': cursor,
          if (type != null && type.isNotEmpty) 'type': type,
          if (status != null && status.isNotEmpty) 'status': status,
          'limit': 10,
        },
      );

      final cached = await _cachedById();
      final items = response.data
          .map((item) =>
              _mergeLocalFilePath(item, cached[item['id'] as String?]))
          .map(reportJobFromJson)
          .toList();

      return PaginatedList(
        items: items,
        nextCursor: response.nextCursor,
        hasMore: response.hasMore,
      );
    } on ApiClientError {
      if (cursor == null) {
        final cachedItems = await getCachedReports();
        return PaginatedList(items: cachedItems, hasMore: false);
      }
      rethrow;
    }
  }

  @override
  Future<ReportJob> generateReport({
    required String type,
    required String locale,
    String? periodId,
    String? classId,
    String? studentId,
    String? parentId,
    String? fromDate,
    String? toDate,
    bool compare = false,
  }) async {
    final response = await _api.post(
      '/reports/generate',
      body: {
        'type': type,
        'locale': locale,
        'compare': compare,
        if (periodId != null && periodId.isNotEmpty) 'period_id': periodId,
        if (classId != null && classId.isNotEmpty) 'class_id': classId,
        if (studentId != null && studentId.isNotEmpty) 'student_id': studentId,
        if (parentId != null && parentId.isNotEmpty) 'parent_id': parentId,
        if (fromDate != null && fromDate.isNotEmpty) 'from_date': fromDate,
        if (toDate != null && toDate.isNotEmpty) 'to_date': toDate,
      },
    );
    return reportJobFromJson(response.data);
  }

  @override
  Future<File> downloadReport(ReportJob job) async {
    if (job.localFilePath != null) {
      final cachedFile = File(job.localFilePath!);
      if (await cachedFile.exists()) {
        return cachedFile;
      }
    }

    if (job.downloadUrl == null || job.downloadUrl!.isEmpty) {
      throw const FileSystemException('Missing download URL');
    }

    final directory = await getApplicationDocumentsDirectory();
    final reportsDir = Directory(p.join(directory.path, 'reports'));
    if (!await reportsDir.exists()) {
      await reportsDir.create(recursive: true);
    }

    final savePath = p.join(reportsDir.path, '${job.id}.pdf');
    final normalizedPath = _normalizeDownloadPath(job.downloadUrl!);
    final file = await _api.download(normalizedPath, savePath: savePath);
    await _reportsStore.upsert(
      {
        'id': job.id,
        'type': job.type,
        'status': job.status,
        'parameters': job.parameters,
        'created_at': job.createdAt,
        'completed_at': job.completedAt,
        'expires_at': job.expiresAt,
        'error_message': job.errorMessage,
        'download_url': job.downloadUrl,
        'cache_hit': job.cacheHit,
        'local_file_path': file.path,
      },
      filePath: file.path,
    );
    return file;
  }

  @override
  Future<List<ReportJob>> getCachedReports() async {
    final rows = await _reportsStore.readAll();
    return rows.map(reportJobFromJson).toList();
  }

  @override
  Future<AnalyticsOverview> getOverview({
    required String fromDate,
    required String toDate,
    required bool compare,
  }) async {
    final response = await _api.get(
      '/analytics/overview',
      params: {
        'from': fromDate,
        'to': toDate,
        'compare': compare.toString(),
      },
    );
    return analyticsOverviewFromJson(response.data);
  }

  @override
  Future<AttendanceAnalytics> getAttendance({
    required String fromDate,
    required String toDate,
    required bool compare,
    required String period,
  }) async {
    final response = await _api.get(
      '/analytics/attendance',
      params: {
        'from': fromDate,
        'to': toDate,
        'compare': compare.toString(),
        'period': period,
      },
    );
    return attendanceAnalyticsFromJson(response.data);
  }

  @override
  Future<GradesAnalytics> getGrades({
    required String fromDate,
    required String toDate,
    required bool compare,
    String? subject,
  }) async {
    final response = await _api.get(
      '/analytics/grades',
      params: {
        'from': fromDate,
        'to': toDate,
        'compare': compare.toString(),
        if (subject != null && subject.isNotEmpty) 'subject': subject,
      },
    );
    return gradesAnalyticsFromJson(response.data);
  }

  @override
  Future<BillingAnalytics> getBilling({
    required String fromDate,
    required String toDate,
    required bool compare,
    required String period,
  }) async {
    final response = await _api.get(
      '/analytics/billing',
      params: {
        'from': fromDate,
        'to': toDate,
        'compare': compare.toString(),
        'period': period,
      },
    );
    return billingAnalyticsFromJson(response.data);
  }

  @override
  Future<EngagementAnalytics> getEngagement({
    required String fromDate,
    required String toDate,
    required bool compare,
  }) async {
    final response = await _api.get(
      '/analytics/engagement',
      params: {
        'from': fromDate,
        'to': toDate,
        'compare': compare.toString(),
      },
    );
    return engagementAnalyticsFromJson(response.data);
  }

  Future<Map<String, Map<String, dynamic>>> _cachedById() async {
    final cached = await _reportsStore.readAll();
    return {
      for (final item in cached)
        if (item['id'] != null) item['id'] as String: item,
    };
  }

  Map<String, dynamic> _mergeLocalFilePath(
    Map<String, dynamic> item,
    Map<String, dynamic>? cached,
  ) {
    if (cached == null || cached['local_file_path'] == null) {
      return item;
    }
    return {
      ...item,
      'local_file_path': cached['local_file_path'],
    };
  }

  String _normalizeDownloadPath(String path) {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    if (path.startsWith('/api/v1/')) {
      return path.substring('/api/v1'.length);
    }
    return path;
  }

  ReportSchedule _scheduleFromJson(Map<String, dynamic> json) {
    return ReportSchedule(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      reportType: json['report_type'] as String? ?? '',
      cronExpression: json['cron_expression'] as String? ?? '',
      parameters: Map<String, dynamic>.from(
        json['parameters'] as Map<String, dynamic>? ?? const {},
      ),
      isActive: json['is_active'] as bool? ?? true,
      createdAt: json['created_at'] as String? ?? '',
      lastRunAt: json['last_run_at'] as String?,
      nextRunAt: json['next_run_at'] as String?,
    );
  }

  @override
  Future<ReportSchedule> createSchedule({
    required String name,
    required String reportType,
    required String cronExpression,
    Map<String, dynamic> parameters = const {},
    bool isActive = true,
  }) async {
    final response = await _api.post(
      '/reports/schedules',
      body: {
        'name': name,
        'report_type': reportType,
        'cron_expression': cronExpression,
        'parameters': parameters,
        'is_active': isActive,
      },
    );
    return _scheduleFromJson(response.data);
  }

  @override
  Future<List<ReportSchedule>> listSchedules() async {
    final response = await _api.list('/reports/schedules');
    return response.data.map(_scheduleFromJson).toList();
  }

  @override
  Future<ReportSchedule> updateSchedule({
    required String id,
    String? name,
    String? reportType,
    String? cronExpression,
    Map<String, dynamic>? parameters,
    bool? isActive,
  }) async {
    final response = await _api.put(
      '/reports/schedules/$id',
      body: {
        if (name != null) 'name': name,
        if (reportType != null) 'report_type': reportType,
        if (cronExpression != null) 'cron_expression': cronExpression,
        if (parameters != null) 'parameters': parameters,
        if (isActive != null) 'is_active': isActive,
      },
    );
    return _scheduleFromJson(response.data);
  }

  @override
  Future<void> deleteSchedule(String scheduleId) async {
    await _api.delete('/reports/schedules/$scheduleId');
  }

  @override
  Future<ReportJob> runSchedule(String scheduleId) async {
    final response = await _api.post(
      '/reports/schedules/$scheduleId/run',
      body: {},
    );
    return reportJobFromJson(response.data);
  }
}
