class RetentionMetric {
  final String label;
  final double rate;

  const RetentionMetric({
    required this.label,
    required this.rate,
  });

  factory RetentionMetric.fromJson(Map<String, dynamic> json) {
    return RetentionMetric(
      label: json['label']?.toString() ??
          json['month']?.toString() ??
          json['period']?.toString() ??
          '',
      rate: (json['rate'] as num?)?.toDouble() ??
          (json['retention_rate'] as num?)?.toDouble() ??
          0,
    );
  }
}

class CashflowForecast {
  final String label;
  final double inflow;
  final double outflow;
  final double net;

  const CashflowForecast({
    required this.label,
    required this.inflow,
    required this.outflow,
    required this.net,
  });

  factory CashflowForecast.fromJson(Map<String, dynamic> json) {
    return CashflowForecast(
      label: json['label']?.toString() ?? json['month']?.toString() ?? '',
      inflow: (json['inflow'] as num?)?.toDouble() ?? 0,
      outflow: (json['outflow'] as num?)?.toDouble() ?? 0,
      net: (json['net'] as num?)?.toDouble() ??
          ((json['inflow'] as num?)?.toDouble() ?? 0) -
              ((json['outflow'] as num?)?.toDouble() ?? 0),
    );
  }
}

class CostPerStudentAnalysis {
  final double costPerStudent;
  final double totalCost;
  final int studentCount;

  const CostPerStudentAnalysis({
    required this.costPerStudent,
    required this.totalCost,
    required this.studentCount,
  });

  factory CostPerStudentAnalysis.fromJson(Map<String, dynamic> json) {
    return CostPerStudentAnalysis(
      costPerStudent:
          (json['cost_per_student'] as num?)?.toDouble() ?? 0,
      totalCost: (json['total_cost'] as num?)?.toDouble() ??
          (json['cost_total'] as num?)?.toDouble() ??
          0,
      studentCount: (json['student_count'] as num?)?.toInt() ?? 0,
    );
  }
}

class FinancialSnapshot {
  final String snapshotDate;
  final double revenue;
  final double expenses;
  final double netPosition;

  const FinancialSnapshot({
    required this.snapshotDate,
    required this.revenue,
    required this.expenses,
    required this.netPosition,
  });

  factory FinancialSnapshot.fromJson(Map<String, dynamic> json) {
    return FinancialSnapshot(
      snapshotDate: json['snapshot_date']?.toString() ??
          json['date']?.toString() ??
          '',
      revenue: (json['revenue'] as num?)?.toDouble() ?? 0,
      expenses: (json['expenses'] as num?)?.toDouble() ?? 0,
      netPosition: (json['net_position'] as num?)?.toDouble() ??
          ((json['revenue'] as num?)?.toDouble() ?? 0) -
              ((json['expenses'] as num?)?.toDouble() ?? 0),
    );
  }
}

class FinancialHealthDashboard {
  final double retentionRate;
  final double netCashflow;
  final double costPerStudent;
  final FinancialSnapshot snapshot;

  const FinancialHealthDashboard({
    required this.retentionRate,
    required this.netCashflow,
    required this.costPerStudent,
    required this.snapshot,
  });

  factory FinancialHealthDashboard.fromJson(Map<String, dynamic> json) {
    return FinancialHealthDashboard(
      retentionRate: (json['retention_rate'] as num?)?.toDouble() ?? 0,
      netCashflow: (json['net_cashflow'] as num?)?.toDouble() ?? 0,
      costPerStudent: (json['cost_per_student'] as num?)?.toDouble() ?? 0,
      snapshot: FinancialSnapshot.fromJson(
        (json['snapshot'] as Map<String, dynamic>?) ?? json,
      ),
    );
  }
}

class FinancialHealthDashboardBundle {
  final FinancialHealthDashboard dashboard;
  final List<RetentionMetric> retention;
  final List<CashflowForecast> cashflow;

  const FinancialHealthDashboardBundle({
    required this.dashboard,
    required this.retention,
    required this.cashflow,
  });
}
