import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/features/gradebook/gradebook_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

class GradeDetailScreen extends ConsumerWidget {
  final String studentId;

  const GradeDetailScreen({
    super.key,
    required this.studentId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(ref);
    final detailAsync = ref.watch(studentGradeDetailProvider(studentId));

    return Scaffold(
      appBar: AppBar(title: Text(t.t('gradebook.studentDetail'))),
      body: detailAsync.when(
        data: (detail) {
          final bars = <BarChartGroupData>[
            for (var index = 0; index < detail.assessments.length; index++)
              BarChartGroupData(
                x: index,
                barRods: [
                  BarChartRodData(
                    toY: detail.assessments[index].score ?? 0,
                    width: 18,
                    color: (detail.assessments[index].score ?? 0) >= 10
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).colorScheme.error,
                    borderRadius: BorderRadius.circular(6),
                  ),
                ],
              ),
          ];

          return ListView(
            padding: const EdgeInsets.all(AppSpacing.base),
            children: [
              AppStatCard(
                label: detail.studentName,
                value: detail.weightedAverage.toStringAsFixed(1),
                icon: Icons.school_outlined,
                trend: detail.weightedAverage >= 10
                    ? TrendDirection.up
                    : TrendDirection.down,
                trendValue: detail.weightedAverage,
              ),
              const SizedBox(height: AppSpacing.base),
              SizedBox(
                height: 220,
                child: BarChart(
                  BarChartData(
                    maxY: 20,
                    borderData: FlBorderData(show: false),
                    gridData: const FlGridData(show: true),
                    barGroups: bars,
                    titlesData: FlTitlesData(
                      leftTitles: AxisTitles(
                        sideTitles: SideTitles(
                          showTitles: true,
                          reservedSize: 30,
                          interval: 5,
                          getTitlesWidget: (value, meta) => Text(
                            value.toInt().toString(),
                            style: Theme.of(context).textTheme.labelSmall,
                          ),
                        ),
                      ),
                      bottomTitles: AxisTitles(
                        sideTitles: SideTitles(
                          showTitles: true,
                          getTitlesWidget: (value, meta) {
                            final index = value.toInt();
                            if (index < 0 || index >= detail.assessments.length) {
                              return const SizedBox.shrink();
                            }
                            return Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Text(
                                detail.assessments[index].title,
                                style: Theme.of(context).textTheme.labelSmall,
                              ),
                            );
                          },
                        ),
                      ),
                      rightTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false),
                      ),
                      topTitles: const AxisTitles(
                        sideTitles: SideTitles(showTitles: false),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.base),
              ...detail.assessments.map(
                (assessment) => Card(
                  child: ListTile(
                    title: Text(assessment.title),
                    subtitle: Text(
                      '${assessment.type} • ${assessment.date}',
                    ),
                    trailing: AppBadge(
                      label: assessment.score?.toStringAsFixed(1) ?? '--',
                      variant: (assessment.score ?? 0) >= 10
                          ? AppBadgeVariant.success
                          : AppBadgeVariant.error,
                    ),
                  ),
                ),
              ),
            ],
          );
        },
        error: (error, _) => AppErrorWidget(message: error.toString()),
        loading: () => const Center(child: CircularProgressIndicator()),
      ),
    );
  }
}
