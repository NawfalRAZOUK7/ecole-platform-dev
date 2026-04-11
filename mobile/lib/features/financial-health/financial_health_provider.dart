import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/financial_health.dart';

final financialAcademicYearIdProvider = Provider<String>((ref) {
  return DateTime.now().year.toString();
});

final financialDashboardProvider =
    FutureProvider<FinancialHealthDashboardBundle>((ref) async {
  final repository = ref.read(financialHealthRepositoryProvider);
  final results = await Future.wait<dynamic>([
    repository.getDashboard(),
    repository.listRetentionMetrics(),
    repository.listCashflowForecasts(),
  ]);
  return FinancialHealthDashboardBundle(
    dashboard: results[0] as FinancialHealthDashboard,
    retention: results[1] as List<RetentionMetric>,
    cashflow: results[2] as List<CashflowForecast>,
  );
});

final financialSnapshotProvider =
    FutureProvider<FinancialSnapshot>((ref) async {
  return ref.read(financialHealthRepositoryProvider).getSnapshot();
});
