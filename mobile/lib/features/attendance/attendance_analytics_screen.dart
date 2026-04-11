import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/attendance.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'attendance_provider.dart';

class AttendanceAnalyticsScreen extends ConsumerStatefulWidget {
  final String? initialClassId;

  const AttendanceAnalyticsScreen({
    super.key,
    this.initialClassId,
  });

  @override
  ConsumerState<AttendanceAnalyticsScreen> createState() =>
      _AttendanceAnalyticsScreenState();
}

class _AttendanceAnalyticsScreenState
    extends ConsumerState<AttendanceAnalyticsScreen> {
  String? _selectedClassId;

  @override
  void initState() {
    super.initState();
    _selectedClassId = widget.initialClassId;
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final classesAsync = ref.watch(attendanceClassesProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('attendance.analytics')),
      ),
      body: classesAsync.when(
        data: (classes) {
          _selectedClassId ??= classes.isNotEmpty ? classes.first.id : null;
          if (_selectedClassId == null) {
            return const AppEmptyState(
              icon: Icons.class_,
              title: 'No classes available',
            );
          }
          final analyticsAsync =
              ref.watch(attendanceAnalyticsProvider(_selectedClassId!));
          return RefreshIndicator(
            onRefresh: () async {
              ref.invalidate(attendanceAnalyticsProvider(_selectedClassId!));
            },
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: DropdownButtonFormField<String>(
                      initialValue: _selectedClassId,
                      decoration: const InputDecoration(
                        labelText: 'Class',
                        border: OutlineInputBorder(),
                      ),
                      items: classes
                          .map(
                            (item) => DropdownMenuItem<String>(
                              value: item.id,
                              child: Text(item.name),
                            ),
                          )
                          .toList(),
                      onChanged: (value) {
                        if (value == null) return;
                        setState(() {
                          _selectedClassId = value;
                        });
                      },
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                analyticsAsync.when(
                  data: (analytics) => _AnalyticsContent(
                    classId: _selectedClassId!,
                    analytics: analytics,
                  ),
                  loading: () => const Padding(
                    padding: EdgeInsets.only(top: 64),
                    child: Center(child: CircularProgressIndicator()),
                  ),
                  error: (error, _) => AppErrorWidget(
                    message: error.toString(),
                  ),
                ),
              ],
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}

class _AnalyticsContent extends ConsumerWidget {
  final String classId;
  final AttendanceAnalyticsBundle analytics;

  const _AnalyticsContent({
    required this.classId,
    required this.analytics,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final repository = ref.read(attendanceRepositoryProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            SizedBox(
              width: 160,
              child: AppStatCard(
                label: 'Attendance rate',
                value: '${analytics.stats.attendanceRate.toStringAsFixed(1)}%',
                icon: Icons.percent,
              ),
            ),
            SizedBox(
              width: 160,
              child: AppStatCard(
                label: 'Sessions',
                value: '${analytics.stats.totalSessions}',
                icon: Icons.event_note,
              ),
            ),
            SizedBox(
              width: 160,
              child: AppStatCard(
                label: 'Absences',
                value: '${analytics.stats.absentCount}',
                icon: Icons.person_off_outlined,
              ),
            ),
            SizedBox(
              width: 160,
              child: AppStatCard(
                label: 'Late / excused',
                value:
                    '${analytics.stats.lateCount + analytics.stats.excusedCount}',
                icon: Icons.schedule,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Attendance trends',
                        style:
                            Theme.of(context).textTheme.titleMedium?.copyWith(
                                  fontWeight: FontWeight.w700,
                                ),
                      ),
                    ),
                    FilledButton.tonalIcon(
                      onPressed: () async {
                        final result = await repository.exportAttendance(
                          classId,
                          format: 'csv',
                        );
                        if (!context.mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text('Export ready: ${result.fileName}'),
                          ),
                        );
                      },
                      icon: const Icon(Icons.download),
                      label: const Text('Export'),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                SizedBox(
                  height: 240,
                  child: _TrendChart(points: analytics.trends),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        Text(
          'Alerts',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w700,
              ),
        ),
        const SizedBox(height: 12),
        if (analytics.alerts.isEmpty)
          const AppEmptyState(
            icon: Icons.shield_outlined,
            title: 'No alerts triggered',
          )
        else
          ...analytics.alerts.map((alert) => _AlertCard(alert: alert)),
      ],
    );
  }
}

class _TrendChart extends StatelessWidget {
  final List<AttendanceTrendPoint> points;

  const _TrendChart({required this.points});

  @override
  Widget build(BuildContext context) {
    if (points.isEmpty) {
      return const AppEmptyState(
        icon: Icons.show_chart,
        title: 'No analytics data available',
      );
    }

    final theme = Theme.of(context);
    return LineChart(
      LineChartData(
        minY: 0,
        maxY: 100,
        gridData: FlGridData(
          show: true,
          horizontalInterval: 20,
          getDrawingHorizontalLine: (_) => FlLine(
            color: theme.colorScheme.outlineVariant,
            strokeWidth: 1,
          ),
        ),
        titlesData: FlTitlesData(
          topTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 42,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= points.length) {
                  return const SizedBox.shrink();
                }
                return SideTitleWidget(
                  axisSide: meta.axisSide,
                  child: Text(
                    points[index].label,
                    style: theme.textTheme.labelSmall,
                  ),
                );
              },
            ),
          ),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              interval: 20,
              getTitlesWidget: (value, meta) => SideTitleWidget(
                axisSide: meta.axisSide,
                child: Text(
                  '${value.toInt()}%',
                  style: theme.textTheme.labelSmall,
                ),
              ),
            ),
          ),
        ),
        borderData: FlBorderData(show: false),
        lineBarsData: [
          LineChartBarData(
            spots: [
              for (var index = 0; index < points.length; index += 1)
                FlSpot(index.toDouble(), points[index].attendanceRate),
            ],
            isCurved: true,
            barWidth: 3,
            color: theme.colorScheme.primary,
            dotData: FlDotData(
              show: true,
              getDotPainter: (_, __, ___, ____) => FlDotCirclePainter(
                radius: 4,
                color: theme.colorScheme.primary,
                strokeColor: theme.colorScheme.surface,
              ),
            ),
            belowBarData: BarAreaData(
              show: true,
              color: theme.colorScheme.primary.withValues(alpha: 0.15),
            ),
          ),
        ],
      ),
    );
  }
}

class _AlertCard extends StatelessWidget {
  final AttendanceAlertItem alert;

  const _AlertCard({required this.alert});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: const Icon(Icons.warning_amber_rounded),
        title: Text(alert.title),
        subtitle: Text(
          '${alert.message}\n${alert.attendanceRate.toStringAsFixed(1)}% / ${alert.threshold.toStringAsFixed(0)}%',
        ),
        trailing: AppBadge(
          label: alert.triggered ? 'Critical' : 'Info',
          variant:
              alert.triggered ? AppBadgeVariant.error : AppBadgeVariant.neutral,
        ),
      ),
    );
  }
}
