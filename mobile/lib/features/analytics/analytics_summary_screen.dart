import 'dart:ui' as ui;

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/reporting.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';

class AnalyticsSummaryScreen extends ConsumerStatefulWidget {
  const AnalyticsSummaryScreen({super.key});

  @override
  ConsumerState<AnalyticsSummaryScreen> createState() =>
      _AnalyticsSummaryScreenState();
}

class _AnalyticsSummaryScreenState
    extends ConsumerState<AnalyticsSummaryScreen> {
  bool _loading = true;
  String? _error;
  String _rangePreset = 'this_month';
  bool _compare = true;
  String _attendancePeriod = 'weekly';
  String _billingPeriod = 'monthly';
  String _subject = '';
  late String _fromDate;
  late String _toDate;
  AnalyticsOverview? _overview;
  AttendanceAnalytics? _attendance;
  GradesAnalytics? _grades;
  BillingAnalytics? _billing;
  EngagementAnalytics? _engagement;

  @override
  void initState() {
    super.initState();
    final range = _buildRange(_rangePreset);
    _fromDate = range.$1;
    _toDate = range.$2;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _load();
    });
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final repo = ref.read(reportingRepositoryProvider);
      final results = await Future.wait([
        repo.getOverview(
          fromDate: _fromDate,
          toDate: _toDate,
          compare: _compare,
        ),
        repo.getAttendance(
          fromDate: _fromDate,
          toDate: _toDate,
          compare: _compare,
          period: _attendancePeriod,
        ),
        repo.getGrades(
          fromDate: _fromDate,
          toDate: _toDate,
          compare: _compare,
          subject: _subject,
        ),
        repo.getBilling(
          fromDate: _fromDate,
          toDate: _toDate,
          compare: _compare,
          period: _billingPeriod,
        ),
        repo.getEngagement(
          fromDate: _fromDate,
          toDate: _toDate,
          compare: _compare,
        ),
      ]);

      setState(() {
        _overview = results[0] as AnalyticsOverview;
        _attendance = results[1] as AttendanceAnalytics;
        _grades = results[2] as GradesAnalytics;
        _billing = results[3] as BillingAnalytics;
        _engagement = results[4] as EngagementAnalytics;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  (String, String) _buildRange(String preset) {
    final now = DateTime.now();
    final today = DateFormat('yyyy-MM-dd').format(now);
    DateTime from;
    switch (preset) {
      case 'this_week':
        from = now.subtract(Duration(days: now.weekday - 1));
        break;
      case 'this_period':
        from = now.subtract(const Duration(days: 29));
        break;
      default:
        from = DateTime(now.year, now.month, 1);
        break;
    }
    return (DateFormat('yyyy-MM-dd').format(from), today);
  }

  void _applyPreset(String preset) {
    final range = _buildRange(preset);
    setState(() {
      _rangePreset = preset;
      _fromDate = range.$1;
      _toDate = range.$2;
    });
    _load();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final role = ref.watch(authProvider).user?.role ?? 'STD';
    final textDirection =
        t.locale == 'ar' ? ui.TextDirection.rtl : ui.TextDirection.ltr;

    if (role != 'ADM' && role != 'DIR') {
      return Directionality(
        textDirection: textDirection,
        child: Scaffold(
          appBar: AppBar(title: Text(t.t('analytics.title'))),
          body: Center(child: Text(t.t('analytics.restricted'))),
        ),
      );
    }

    return Directionality(
      textDirection: textDirection,
      child: Scaffold(
        appBar: AppBar(
          title: Text(t.t('analytics.title')),
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: _load,
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    if (_error != null) ...[
                      Card(
                        color: Colors.red.shade50,
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Text(
                            _error!,
                            style: const TextStyle(color: Colors.red),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                    ],
                    _buildToolbar(t),
                    const SizedBox(height: 16),
                    _buildKpis(t),
                    const SizedBox(height: 16),
                    _buildAttendanceCard(t),
                    const SizedBox(height: 16),
                    _buildGradesCard(t),
                    const SizedBox(height: 16),
                    _buildBillingCard(t),
                    const SizedBox(height: 16),
                    _buildEngagementCard(t),
                  ],
                ),
              ),
      ),
    );
  }

  Widget _buildToolbar(AppLocalizations t) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${_fromDate} → $_toDate',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _PresetChip(
                  label: t.t('analytics.presets.this_week'),
                  selected: _rangePreset == 'this_week',
                  onTap: () => _applyPreset('this_week'),
                ),
                _PresetChip(
                  label: t.t('analytics.presets.this_month'),
                  selected: _rangePreset == 'this_month',
                  onTap: () => _applyPreset('this_month'),
                ),
                _PresetChip(
                  label: t.t('analytics.presets.this_period'),
                  selected: _rangePreset == 'this_period',
                  onTap: () => _applyPreset('this_period'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              value: _compare,
              title: Text(t.t('analytics.compare')),
              onChanged: (value) {
                setState(() => _compare = value);
                _load();
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildKpis(AppLocalizations t) {
    final metrics = _overview?.metrics ?? const {};
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        _MetricCard(
          title: t.t('analytics.kpis.activeUsers'),
          metric: metrics['active_users'] ?? const AnalyticsMetric(current: 0),
          suffix: '',
          onTap: () => _showDetailSheet(
            title: t.t('analytics.kpis.activeUsers'),
            child: _FunnelChartCard(funnel: _engagement?.funnel ?? const []),
          ),
        ),
        _MetricCard(
          title: t.t('analytics.kpis.attendanceRate'),
          metric:
              metrics['attendance_rate'] ?? const AnalyticsMetric(current: 0),
          suffix: '%',
          onTap: () => _showDetailSheet(
            title: t.t('analytics.kpis.attendanceRate'),
            child: _AttendanceChart(series: _attendance?.series ?? const []),
          ),
        ),
        _MetricCard(
          title: t.t('analytics.kpis.averageGrade'),
          metric: metrics['average_grade'] ?? const AnalyticsMetric(current: 0),
          suffix: '',
          onTap: () => _showDetailSheet(
            title: t.t('analytics.kpis.averageGrade'),
            child: _DistributionChart(
              buckets: _grades?.distribution ?? const [],
              color: Colors.green,
            ),
          ),
        ),
        _MetricCard(
          title: t.t('analytics.kpis.collectionRate'),
          metric:
              metrics['collection_rate'] ?? const AnalyticsMetric(current: 0),
          suffix: '%',
          onTap: () => _showDetailSheet(
            title: t.t('analytics.kpis.collectionRate'),
            child: _WaterfallChart(
              values: [
                _billing?.invoiced ?? 0,
                _billing?.paid ?? 0,
                _billing?.outstanding ?? 0,
              ],
              labels: [
                t.t('analytics.stages.invoiced'),
                t.t('analytics.stages.paid'),
                t.t('analytics.stages.outstanding'),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildAttendanceCard(AppLocalizations t) {
    return _SectionCard(
      title: t.t('analytics.charts.attendance'),
      subtitle: t.t('analytics.buckets.$_attendancePeriod'),
      action: DropdownButton<String>(
        value: _attendancePeriod,
        underline: const SizedBox.shrink(),
        items: ['daily', 'weekly', 'monthly']
            .map(
              (item) => DropdownMenuItem(
                value: item,
                child: Text(t.t('analytics.buckets.$item')),
              ),
            )
            .toList(),
        onChanged: (value) {
          if (value == null) return;
          setState(() => _attendancePeriod = value);
          _load();
        },
      ),
      child: _AttendanceChart(series: _attendance?.series ?? const []),
    );
  }

  Widget _buildGradesCard(AppLocalizations t) {
    return _SectionCard(
      title: t.t('analytics.charts.grades'),
      subtitle: t.t('analytics.subjectHint'),
      action: SizedBox(
        width: 140,
        child: TextField(
          controller: TextEditingController(text: _subject),
          decoration: InputDecoration(
            hintText: t.t('analytics.subjectPlaceholder'),
            isDense: true,
          ),
          onSubmitted: (value) {
            setState(() => _subject = value);
            _load();
          },
        ),
      ),
      child: _DistributionChart(
        buckets: _grades?.distribution ?? const [],
        color: Colors.green,
      ),
    );
  }

  Widget _buildBillingCard(AppLocalizations t) {
    return _SectionCard(
      title: t.t('analytics.charts.billing'),
      subtitle: t.t('analytics.buckets.$_billingPeriod'),
      action: DropdownButton<String>(
        value: _billingPeriod,
        underline: const SizedBox.shrink(),
        items: ['daily', 'weekly', 'monthly']
            .map(
              (item) => DropdownMenuItem(
                value: item,
                child: Text(t.t('analytics.buckets.$item')),
              ),
            )
            .toList(),
        onChanged: (value) {
          if (value == null) return;
          setState(() => _billingPeriod = value);
          _load();
        },
      ),
      child: _WaterfallChart(
        values: [
          _billing?.invoiced ?? 0,
          _billing?.paid ?? 0,
          _billing?.outstanding ?? 0,
        ],
        labels: [
          t.t('analytics.stages.invoiced'),
          t.t('analytics.stages.paid'),
          t.t('analytics.stages.outstanding'),
        ],
      ),
    );
  }

  Widget _buildEngagementCard(AppLocalizations t) {
    return _SectionCard(
      title: t.t('analytics.charts.engagement'),
      subtitle: t.t('analytics.charts.engagementHint'),
      child: _FunnelChartCard(funnel: _engagement?.funnel ?? const []),
    );
  }

  void _showDetailSheet({
    required String title,
    required Widget child,
  }) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 16),
                SizedBox(height: 260, child: child),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String title;
  final AnalyticsMetric metric;
  final String suffix;
  final VoidCallback onTap;

  const _MetricCard({
    required this.title,
    required this.metric,
    required this.suffix,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final values = [
      metric.previous ?? metric.current,
      metric.current,
    ];
    final delta = metric.changePercent;
    final deltaColor = switch (metric.trend) {
      'up' => Colors.green,
      'down' => Colors.red,
      _ => Colors.grey,
    };

    return SizedBox(
      width: 172,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.bodyMedium),
                const SizedBox(height: 8),
                Text(
                  '${metric.current.toStringAsFixed(1)}$suffix',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  delta == null ? '—' : '${delta.toStringAsFixed(1)}%',
                  style: TextStyle(
                    color: deltaColor,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 8),
                SizedBox(
                  height: 40,
                  child: LineChart(
                    LineChartData(
                      minX: 0,
                      maxX: 1,
                      minY: 0,
                      maxY: (values.reduce((a, b) => a > b ? a : b) * 1.2)
                          .clamp(1, double.infinity),
                      gridData: const FlGridData(show: false),
                      titlesData: const FlTitlesData(show: false),
                      borderData: FlBorderData(show: false),
                      lineBarsData: [
                        LineChartBarData(
                          isCurved: true,
                          spots: [
                            FlSpot(0, values[0]),
                            FlSpot(1, values[1]),
                          ],
                          color: deltaColor,
                          barWidth: 3,
                          dotData: const FlDotData(show: false),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final Widget child;
  final Widget? action;

  const _SectionCard({
    required this.title,
    required this.subtitle,
    required this.child,
    this.action,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        subtitle,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                if (action != null) action!,
              ],
            ),
            const SizedBox(height: 16),
            SizedBox(height: 220, child: child),
          ],
        ),
      ),
    );
  }
}

class _AttendanceChart extends StatelessWidget {
  final List<AnalyticsSeriesPoint> series;

  const _AttendanceChart({required this.series});

  @override
  Widget build(BuildContext context) {
    if (series.isEmpty) {
      return const Center(child: Text('—'));
    }

    final maxValue = series
        .map((item) => item.value)
        .fold<double>(0, (a, b) => a > b ? a : b);

    return LineChart(
      LineChartData(
        minY: 0,
        maxY: (maxValue * 1.2).clamp(1, 100),
        gridData: const FlGridData(show: true),
        titlesData: FlTitlesData(
          topTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: true, reservedSize: 32),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= series.length) {
                  return const SizedBox.shrink();
                }
                return Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    series[index].label,
                    style: const TextStyle(fontSize: 10),
                  ),
                );
              },
            ),
          ),
        ),
        lineBarsData: [
          LineChartBarData(
            spots: series
                .asMap()
                .entries
                .map((entry) => FlSpot(entry.key.toDouble(), entry.value.value))
                .toList(),
            isCurved: true,
            color: Colors.blue,
            barWidth: 3,
            dotData: const FlDotData(show: true),
            belowBarData: BarAreaData(
              show: true,
              color: Colors.blue.withAlpha(24),
            ),
          ),
        ],
      ),
    );
  }
}

class _DistributionChart extends StatelessWidget {
  final List<AnalyticsBucket> buckets;
  final Color color;

  const _DistributionChart({
    required this.buckets,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    if (buckets.isEmpty) {
      return const Center(child: Text('—'));
    }

    final maxValue = buckets
        .map((item) => item.count.toDouble())
        .fold<double>(0, (a, b) => a > b ? a : b);

    return BarChart(
      BarChartData(
        maxY: (maxValue * 1.2).clamp(1, double.infinity),
        gridData: const FlGridData(show: true),
        titlesData: FlTitlesData(
          topTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: true, reservedSize: 28),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= buckets.length) {
                  return const SizedBox.shrink();
                }
                return Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    buckets[index].label,
                    style: const TextStyle(fontSize: 10),
                  ),
                );
              },
            ),
          ),
        ),
        borderData: FlBorderData(show: false),
        barGroups: buckets
            .asMap()
            .entries
            .map(
              (entry) => BarChartGroupData(
                x: entry.key,
                barRods: [
                  BarChartRodData(
                    toY: entry.value.count.toDouble(),
                    color: color,
                    width: 18,
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(6),
                    ),
                  ),
                ],
              ),
            )
            .toList(),
      ),
    );
  }
}

class _WaterfallChart extends StatelessWidget {
  final List<double> values;
  final List<String> labels;

  const _WaterfallChart({
    required this.values,
    required this.labels,
  });

  @override
  Widget build(BuildContext context) {
    final colors = [Colors.indigo, Colors.green, Colors.orange];
    final maxValue = values.fold<double>(0, (a, b) => a > b ? a : b);

    return BarChart(
      BarChartData(
        maxY: (maxValue * 1.2).clamp(1, double.infinity),
        gridData: const FlGridData(show: true),
        titlesData: FlTitlesData(
          topTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: true, reservedSize: 32),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= labels.length) {
                  return const SizedBox.shrink();
                }
                return Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    labels[index],
                    style: const TextStyle(fontSize: 10),
                  ),
                );
              },
            ),
          ),
        ),
        barGroups: values
            .asMap()
            .entries
            .map(
              (entry) => BarChartGroupData(
                x: entry.key,
                barRods: [
                  BarChartRodData(
                    toY: entry.value,
                    color: colors[entry.key % colors.length],
                    width: 18,
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(6),
                    ),
                  ),
                ],
              ),
            )
            .toList(),
      ),
    );
  }
}

class _FunnelChartCard extends StatelessWidget {
  final List<FunnelStage> funnel;

  const _FunnelChartCard({required this.funnel});

  @override
  Widget build(BuildContext context) {
    if (funnel.isEmpty) {
      return const Center(child: Text('—'));
    }

    final maxValue = funnel
        .map((item) => item.value.toDouble())
        .fold<double>(0, (a, b) => a > b ? a : b);

    return BarChart(
      BarChartData(
        maxY: (maxValue * 1.2).clamp(1, double.infinity),
        gridData: const FlGridData(show: true),
        titlesData: FlTitlesData(
          topTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles:
              const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: true, reservedSize: 32),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 30,
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index < 0 || index >= funnel.length) {
                  return const SizedBox.shrink();
                }
                return Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    funnel[index].label,
                    style: const TextStyle(fontSize: 10),
                  ),
                );
              },
            ),
          ),
        ),
        barGroups: funnel
            .asMap()
            .entries
            .map(
              (entry) => BarChartGroupData(
                x: entry.key,
                barRods: [
                  BarChartRodData(
                    toY: entry.value.value.toDouble(),
                    color: Colors.deepPurple,
                    width: 18,
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(6),
                    ),
                  ),
                ],
              ),
            )
            .toList(),
      ),
    );
  }
}

class _PresetChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _PresetChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => onTap(),
    );
  }
}
