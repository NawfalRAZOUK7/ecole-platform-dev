import 'package:fl_chart/fl_chart.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/domain/entities/financial_health.dart';
import 'package:ecole_platform/features/financial-health/financial_dashboard_screen.dart';
import 'package:ecole_platform/features/financial-health/financial_snapshots_screen.dart';

import '../helpers/mock_repositories.dart';
import '../helpers/pump_app.dart';
import '../helpers/test_mocks.dart';

void main() {
  setUpAll(registerTestFallbacks);

  testWidgets('FinancialDashboardScreen renders charts', (tester) async {
    final repository = MockFinancialHealthRepository();
    _stubDashboard(repository);

    await pumpApp(
      tester,
      const FinancialDashboardScreen(),
      overrides: buildMockRepositoryOverrides(
        financialHealthRepository: repository,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(LineChart), findsOneWidget);
    expect(find.byType(BarChart), findsOneWidget);
  });

  testWidgets('FinancialDashboardScreen renders stats and export actions',
      (tester) async {
    final repository = MockFinancialHealthRepository();
    _stubDashboard(repository);

    await pumpApp(
      tester,
      const FinancialDashboardScreen(),
      overrides: buildMockRepositoryOverrides(
        financialHealthRepository: repository,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Retention'), findsOneWidget);
    expect(find.text('Net cashflow'), findsOneWidget);
    expect(find.text('Cost / student'), findsOneWidget);
  });

  testWidgets('FinancialSnapshotsScreen renders snapshot list', (tester) async {
    final repository = MockFinancialHealthRepository();
    when(() => repository.getSnapshot()).thenAnswer((_) async => _snapshot);

    await pumpApp(
      tester,
      const FinancialSnapshotsScreen(),
      overrides: buildMockRepositoryOverrides(
        financialHealthRepository: repository,
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('2026-04-12'), findsOneWidget);
    expect(find.textContaining('Revenue 120000'), findsOneWidget);
  });
}

void _stubDashboard(MockFinancialHealthRepository repository) {
  when(() => repository.getDashboard()).thenAnswer(
    (_) async => const FinancialHealthDashboard(
      retentionRate: 92.5,
      netCashflow: 24000,
      costPerStudent: 5800,
      snapshot: _snapshot,
    ),
  );
  when(() => repository.listRetentionMetrics()).thenAnswer(
    (_) async => const [
      RetentionMetric(label: 'Jan', rate: 91),
      RetentionMetric(label: 'Feb', rate: 92),
    ],
  );
  when(() => repository.listCashflowForecasts()).thenAnswer(
    (_) async => const [
      CashflowForecast(
          label: 'Jan', inflow: 100000, outflow: 80000, net: 20000),
      CashflowForecast(
          label: 'Feb', inflow: 105000, outflow: 81000, net: 24000),
    ],
  );
}

const _snapshot = FinancialSnapshot(
  snapshotDate: '2026-04-12',
  revenue: 120000,
  expenses: 98000,
  netPosition: 22000,
);
