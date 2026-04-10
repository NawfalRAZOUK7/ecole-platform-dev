import 'dart:io';

import 'package:ecole_platform/domain/entities/financial_health.dart';

abstract class FinancialHealthRepository {
  Future<List<RetentionMetric>> listRetentionMetrics({Map<String, dynamic>? params});

  Future<RetentionMetric> computeRetention(Map<String, dynamic> payload);

  Future<List<CashflowForecast>> listCashflowForecasts({
    Map<String, dynamic>? params,
  });

  Future<List<CashflowForecast>> computeCashflow(Map<String, dynamic> payload);

  Future<CostPerStudentAnalysis> getCostPerStudent(String academicYearId);

  Future<CostPerStudentAnalysis> computeCostPerStudent(Map<String, dynamic> payload);

  Future<FinancialSnapshot> getSnapshot({String? snapshotDate});

  Future<FinancialSnapshot> computeSnapshot(Map<String, dynamic> payload);

  Future<FinancialHealthDashboard> getDashboard();

  Future<List<Map<String, dynamic>>> getTrends({int months = 12});

  Future<File> exportCsv();

  Future<File> exportPdf();
}
