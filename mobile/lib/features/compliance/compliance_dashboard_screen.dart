import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'compliance_provider.dart';

class ComplianceDashboardScreen extends ConsumerWidget {
  const ComplianceDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboardAsync = ref.watch(complianceDashboardProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('compliance.dashboard'))),
      body: dashboardAsync.when(
        data: (dashboard) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                _GaugeCard(
                  label: t.t('compliance.coverage'),
                  value: dashboard.coverageRate,
                ),
                _GaugeCard(
                  label: t.t('compliance.objectives'),
                  value: dashboard.objectivesCoveredRate,
                ),
                _GaugeCard(
                  label: t.t('compliance.gaps'),
                  value: dashboard.missingCoverageRate,
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...dashboard.metrics.map(
              (metric) => Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  title: Text(metric.label),
                  trailing: Text('${metric.value.toStringAsFixed(0)}%'),
                ),
              ),
            ),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}

class _GaugeCard extends StatelessWidget {
  final String label;
  final double value;

  const _GaugeCard({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 170,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              SizedBox(
                width: 84,
                height: 84,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    CircularProgressIndicator(
                      value: (value / 100).clamp(0, 1),
                      strokeWidth: 8,
                    ),
                    Text('${value.toStringAsFixed(0)}%'),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Text(label, textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}
