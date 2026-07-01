import 'dart:io';

import 'package:ecole_platform/domain/entities/reports/reporting.dart';
import 'package:ecole_platform/domain/common/pagination.dart';

abstract class ReportingRepository {
  Future<ReportOptions> getReportOptions({
    String? type,
    String? classId,
  });

  Future<PaginatedList<ReportJob>> getReportJobs({
    String? cursor,
    String? type,
    String? status,
  });

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
  });

  Future<File> downloadReport(ReportJob job);

  Future<List<ReportJob>> getCachedReports();

  Future<ReportSchedule> createSchedule({
    required String name,
    required String reportType,
    required String cronExpression,
    Map<String, dynamic> parameters = const {},
    bool isActive = true,
  });

  Future<List<ReportSchedule>> listSchedules();

  Future<ReportSchedule> updateSchedule({
    required String id,
    String? name,
    String? reportType,
    String? cronExpression,
    Map<String, dynamic>? parameters,
    bool? isActive,
  });

  Future<void> deleteSchedule(String scheduleId);

  Future<ReportJob> runSchedule(String scheduleId);

  Future<AnalyticsOverview> getOverview({
    required String fromDate,
    required String toDate,
    required bool compare,
  });

  Future<AttendanceAnalytics> getAttendance({
    required String fromDate,
    required String toDate,
    required bool compare,
    required String period,
  });

  Future<GradesAnalytics> getGrades({
    required String fromDate,
    required String toDate,
    required bool compare,
    String? subject,
  });

  Future<BillingAnalytics> getBilling({
    required String fromDate,
    required String toDate,
    required bool compare,
    required String period,
  });

  Future<EngagementAnalytics> getEngagement({
    required String fromDate,
    required String toDate,
    required bool compare,
  });
}
