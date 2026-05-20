/// Reporting entities for Phase 14 mobile flows.

class ReportOptionItem {
  final String id;
  final String label;
  final String? secondary;

  const ReportOptionItem({
    required this.id,
    required this.label,
    this.secondary,
  });
}

class ReportOptions {
  final List<ReportOptionItem> classes;
  final List<ReportOptionItem> periods;
  final List<ReportOptionItem> students;
  final List<ReportOptionItem> parents;

  const ReportOptions({
    this.classes = const [],
    this.periods = const [],
    this.students = const [],
    this.parents = const [],
  });
}

class ReportJob {
  final String id;
  final String type;
  final String status;
  final Map<String, dynamic> parameters;
  final String createdAt;
  final String? completedAt;
  final String? expiresAt;
  final String? errorMessage;
  final String? downloadUrl;
  final bool cacheHit;
  final String? localFilePath;

  const ReportJob({
    required this.id,
    required this.type,
    required this.status,
    required this.parameters,
    required this.createdAt,
    this.completedAt,
    this.expiresAt,
    this.errorMessage,
    this.downloadUrl,
    this.cacheHit = false,
    this.localFilePath,
  });

  bool get isReady => status == 'ready';
  bool get isPending => status == 'pending' || status == 'generating';

  ReportJob copyWith({
    String? id,
    String? type,
    String? status,
    Map<String, dynamic>? parameters,
    String? createdAt,
    String? completedAt,
    String? expiresAt,
    String? errorMessage,
    String? downloadUrl,
    bool? cacheHit,
    String? localFilePath,
  }) {
    return ReportJob(
      id: id ?? this.id,
      type: type ?? this.type,
      status: status ?? this.status,
      parameters: parameters ?? this.parameters,
      createdAt: createdAt ?? this.createdAt,
      completedAt: completedAt ?? this.completedAt,
      expiresAt: expiresAt ?? this.expiresAt,
      errorMessage: errorMessage ?? this.errorMessage,
      downloadUrl: downloadUrl ?? this.downloadUrl,
      cacheHit: cacheHit ?? this.cacheHit,
      localFilePath: localFilePath ?? this.localFilePath,
    );
  }
}

class ReportSchedule {
  final String id;
  final String name;
  final String reportType;
  final String cronExpression;
  final Map<String, dynamic> parameters;
  final bool isActive;
  final String createdAt;
  final String? lastRunAt;
  final String? nextRunAt;

  const ReportSchedule({
    required this.id,
    required this.name,
    required this.reportType,
    required this.cronExpression,
    required this.parameters,
    required this.isActive,
    required this.createdAt,
    this.lastRunAt,
    this.nextRunAt,
  });
}

class AnalyticsMetric {
  final double current;
  final double? previous;
  final double? changePercent;
  final String trend;

  const AnalyticsMetric({
    required this.current,
    this.previous,
    this.changePercent,
    this.trend = 'flat',
  });
}

class AnalyticsSeriesPoint {
  final String label;
  final double value;
  final Map<String, dynamic> extra;

  const AnalyticsSeriesPoint({
    required this.label,
    required this.value,
    this.extra = const {},
  });
}

class AnalyticsBucket {
  final String label;
  final int count;

  const AnalyticsBucket({
    required this.label,
    required this.count,
  });
}

class AnalyticsOverview {
  final Map<String, AnalyticsMetric> metrics;

  const AnalyticsOverview({required this.metrics});
}

class AttendanceAnalytics {
  final AnalyticsMetric rate;
  final int totalRecords;
  final List<AnalyticsSeriesPoint> series;

  const AttendanceAnalytics({
    required this.rate,
    required this.totalRecords,
    required this.series,
  });
}

class GradesAnalytics {
  final AnalyticsMetric average;
  final int count;
  final List<AnalyticsBucket> distribution;

  const GradesAnalytics({
    required this.average,
    required this.count,
    required this.distribution,
  });
}

class BillingAnalytics {
  final double invoiced;
  final double paid;
  final double outstanding;
  final AnalyticsMetric collectionRate;
  final List<AnalyticsSeriesPoint> series;

  const BillingAnalytics({
    required this.invoiced,
    required this.paid,
    required this.outstanding,
    required this.collectionRate,
    required this.series,
  });
}

class FunnelStage {
  final String label;
  final int value;

  const FunnelStage({
    required this.label,
    required this.value,
  });
}

class FeatureAdoptionMetric {
  final String feature;
  final int users;
  final double adoptionRate;

  const FeatureAdoptionMetric({
    required this.feature,
    required this.users,
    required this.adoptionRate,
  });
}

class EngagementAnalytics {
  final int registeredUsers;
  final int dau;
  final int mau;
  final AnalyticsMetric activeUsers;
  final int engagedUsers;
  final List<FunnelStage> funnel;
  final List<FeatureAdoptionMetric> featureAdoption;

  const EngagementAnalytics({
    required this.registeredUsers,
    required this.dau,
    required this.mau,
    required this.activeUsers,
    required this.engagedUsers,
    required this.funnel,
    required this.featureAdoption,
  });
}
