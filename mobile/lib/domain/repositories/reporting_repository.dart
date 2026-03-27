import 'dart:io';

import 'package:ecole_platform/domain/entities/reporting.dart';
import 'package:ecole_platform/domain/repositories/feed_repository.dart';

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
