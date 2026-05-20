import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/reports/financial_health.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'financial_health_provider.dart';

class FinancialDashboardScreen extends ConsumerWidget {
  const FinancialDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboardAsync = ref.watch(financialDashboardProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('financialHealth.dashboard')),
        actions: [
          IconButton(
            onPressed: () => context.push('/financial-health/snapshots'),
            icon: const Icon(Icons.history_outlined),
          ),
        ],
      ),
      body: dashboardAsync.when(
        data: (bundle) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                SizedBox(
                  width: 170,
                  child: AppStatCard(
                    label: 'Retention',
                    value:
                        '${bundle.dashboard.retentionRate.toStringAsFixed(1)}%',
                    icon: Icons.favorite_outline,
                  ),
                ),
                SizedBox(
                  width: 170,
                  child: AppStatCard(
                    label: 'Net cashflow',
                    value: bundle.dashboard.netCashflow.toStringAsFixed(0),
                    icon: Icons.account_balance_wallet_outlined,
                  ),
                ),
                SizedBox(
                  width: 170,
                  child: AppStatCard(
                    label: 'Cost / student',
                    value: bundle.dashboard.costPerStudent.toStringAsFixed(0),
                    icon: Icons.school_outlined,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: SizedBox(
                  height: 220,
                  child: _CashflowChart(points: bundle.cashflow),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: SizedBox(
                  height: 220,
                  child: _RetentionChart(points: bundle.retention),
                ),
              ),
            ),
            const SizedBox(height: 16),
            const FinancialExportScreen(),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}

class FinancialExportScreen extends ConsumerWidget {
  const FinancialExportScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: FilledButton.tonalIcon(
                onPressed: () async {
                  final file = await ref
                      .read(financialHealthRepositoryProvider)
                      .exportCsv();
                  if (!context.mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('CSV exported: ${file.path}')),
                  );
                },
                icon: const Icon(Icons.table_chart_outlined),
                label: const Text('CSV'),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: FilledButton.tonalIcon(
                onPressed: () async {
                  final file = await ref
                      .read(financialHealthRepositoryProvider)
                      .exportPdf();
                  if (!context.mounted) return;
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('PDF exported: ${file.path}')),
                  );
                },
                icon: const Icon(Icons.picture_as_pdf_outlined),
                label: const Text('PDF'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CashflowChart extends StatelessWidget {
  final List<CashflowForecast> points;

  const _CashflowChart({required this.points});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return LineChart(
      LineChartData(
        borderData: FlBorderData(show: false),
        gridData: const FlGridData(show: true),
        lineBarsData: [
          LineChartBarData(
            spots: [
              for (var i = 0; i < points.length; i += 1)
                FlSpot(i.toDouble(), points[i].net),
            ],
            isCurved: true,
            color: theme.colorScheme.primary,
          ),
        ],
        titlesData: const FlTitlesData(
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
      ),
    );
  }
}

class _RetentionChart extends StatelessWidget {
  final List<RetentionMetric> points;

  const _RetentionChart({required this.points});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return BarChart(
      BarChartData(
        borderData: FlBorderData(show: false),
        gridData: const FlGridData(show: true),
        titlesData: const FlTitlesData(
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        barGroups: [
          for (var i = 0; i < points.length; i += 1)
            BarChartGroupData(
              x: i,
              barRods: [
                BarChartRodData(
                  toY: points[i].rate,
                  color: theme.colorScheme.tertiary,
                ),
              ],
            ),
        ],
      ),
    );
  }
}
