/// Progress screen — 4 chart tabs using fl_chart (grade trend, content, activity, attendance).
///
/// Reference: Phase 12C — Mobile progress dashboard
/// STD sees own progress, PAR can pass studentId for child detail.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'progress_provider.dart';

/// Student progress dashboard with 4 tabbed chart views (grades, content,
/// activities, attendance) rendered using fl_chart.
///
/// When [studentId] is null the screen shows the authenticated student's own
/// progress; when provided it shows the specified student's data (parent
/// drill-down).
///
/// Roles: STD, PAR.
class ProgressScreen extends ConsumerStatefulWidget {
  /// Optional student ID for parent drill-down. Null means "my own progress".
  final String? studentId;
  const ProgressScreen({super.key, this.studentId});

  @override
  ConsumerState<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends ConsumerState<ProgressScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(progressProvider(widget.studentId));
    final t = AppLocalizations.of(ref);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(state.progress != null && widget.studentId != null
            ? state.progress!.studentName
            : t.t('progress.title')),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: [
            Tab(text: t.t('progress.grades')),
            Tab(text: t.t('progress.content')),
            Tab(text: t.t('progress.activities')),
            Tab(text: t.t('progress.attendance')),
          ],
        ),
      ),
      body: _buildBody(state, t, theme),
    );
  }

  Widget _buildBody(ProgressState state, AppLocalizations t, ThemeData theme) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () =>
                  ref.read(progressProvider(widget.studentId).notifier).load(),
              child: Text(t.t('common.retry')),
            ),
          ],
        ),
      );
    }

    final p = state.progress;
    if (p == null) return const SizedBox.shrink();

    return RefreshIndicator(
      onRefresh: () =>
          ref.read(progressProvider(widget.studentId).notifier).load(),
      child: TabBarView(
        controller: _tabController,
        children: [
          _GradeTab(progress: p, t: t, theme: theme),
          _ContentTab(progress: p, t: t, theme: theme),
          _ActivityTab(progress: p, t: t, theme: theme),
          _AttendanceTab(progress: p, t: t, theme: theme),
        ],
      ),
    );
  }
}

// ── Grade Trend Tab (Line Chart) ──

/// Displays a line chart of grade averages over time with a summary row.
class _GradeTab extends StatelessWidget {
  final StudentProgress progress;
  final AppLocalizations t;
  final ThemeData theme;
  const _GradeTab({required this.progress, required this.t, required this.theme});

  @override
  Widget build(BuildContext context) {
    final ds = progress.gradeTrends.datasets.isNotEmpty
        ? progress.gradeTrends.datasets[0]
        : null;
    if (ds == null || ds.data.isEmpty) {
      return Center(child: Text(t.t('progress.noData')));
    }

    final spots = ds.data
        .asMap()
        .entries
        .map((e) => FlSpot(e.key.toDouble(), e.value))
        .toList();

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(t.t('progress.gradeTrend'),
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          _summaryRow(t.t('progress.gradeAvg'),
              (ds.data.reduce((a, b) => a + b) / ds.data.length).toStringAsFixed(1)),
          const SizedBox(height: 16),
          Expanded(
            child: LineChart(
              LineChartData(
                minY: 0,
                maxY: 100,
                gridData: const FlGridData(show: true),
                titlesData: FlTitlesData(
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 30,
                      getTitlesWidget: (value, meta) {
                        final idx = value.toInt();
                        if (idx < 0 || idx >= progress.gradeTrends.labels.length) {
                          return const SizedBox.shrink();
                        }
                        return Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(progress.gradeTrends.labels[idx],
                              style: const TextStyle(fontSize: 10)),
                        );
                      },
                    ),
                  ),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(showTitles: true, reservedSize: 35),
                  ),
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                borderData: FlBorderData(show: true),
                lineBarsData: [
                  LineChartBarData(
                    spots: spots,
                    isCurved: true,
                    color: theme.colorScheme.primary,
                    barWidth: 3,
                    dotData: const FlDotData(show: true),
                    belowBarData: BarAreaData(
                      show: true,
                      color: theme.colorScheme.primary.withAlpha(30),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _summaryRow(String label, String value) => Row(
        children: [
          Text(label, style: theme.textTheme.bodyMedium),
          const SizedBox(width: 8),
          Text(value,
              style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
        ],
      );
}

// ── Content Completion Tab (Pie Chart) ──

/// Displays a donut pie chart of content completion status with a legend.
class _ContentTab extends StatelessWidget {
  final StudentProgress progress;
  final AppLocalizations t;
  final ThemeData theme;
  const _ContentTab({required this.progress, required this.t, required this.theme});

  @override
  Widget build(BuildContext context) {
    final ds = progress.contentCompletion.datasets.isNotEmpty
        ? progress.contentCompletion.datasets[0]
        : null;
    if (ds == null || ds.data.every((v) => v == 0)) {
      return Center(child: Text(t.t('progress.noData')));
    }

    final colors = [const Color(0xFF10b981), const Color(0xFFf59e0b), const Color(0xFFef4444)];
    final sections = ds.data.asMap().entries.map((e) {
      return PieChartSectionData(
        value: e.value,
        color: colors[e.key % colors.length],
        title: '${e.value.toInt()}',
        radius: 60,
        titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
      );
    }).toList();

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Text(t.t('progress.contentCompletion'),
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(
            '${progress.contentSummary.completionRate.toStringAsFixed(0)}% (${progress.contentSummary.completed}/${progress.contentSummary.total})',
            style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: PieChart(
              PieChartData(
                sections: sections,
                centerSpaceRadius: 50,
                sectionsSpace: 2,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: progress.contentCompletion.labels.asMap().entries.map((e) {
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: Row(children: [
                  Container(width: 12, height: 12, color: colors[e.key % colors.length]),
                  const SizedBox(width: 4),
                  Text(e.value, style: const TextStyle(fontSize: 12)),
                ]),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }
}

// ── Activity Scores Tab (Bar Chart) ──

/// Displays a vertical bar chart of activity scores by period.
class _ActivityTab extends StatelessWidget {
  final StudentProgress progress;
  final AppLocalizations t;
  final ThemeData theme;
  const _ActivityTab({required this.progress, required this.t, required this.theme});

  @override
  Widget build(BuildContext context) {
    final ds = progress.activityScores.datasets.isNotEmpty
        ? progress.activityScores.datasets[0]
        : null;
    if (ds == null || ds.data.isEmpty) {
      return Center(child: Text(t.t('progress.noData')));
    }

    final barGroups = ds.data.asMap().entries.map((e) {
      return BarChartGroupData(x: e.key, barRods: [
        BarChartRodData(
          toY: e.value,
          color: const Color(0xFF8b5cf6),
          width: 20,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
        ),
      ]);
    }).toList();

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(t.t('progress.activityScores'),
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          Expanded(
            child: BarChart(
              BarChartData(
                maxY: 100,
                gridData: const FlGridData(show: true),
                titlesData: FlTitlesData(
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 30,
                      getTitlesWidget: (value, meta) {
                        final idx = value.toInt();
                        if (idx < 0 || idx >= progress.activityScores.labels.length) {
                          return const SizedBox.shrink();
                        }
                        return Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Text(progress.activityScores.labels[idx],
                              style: const TextStyle(fontSize: 10)),
                        );
                      },
                    ),
                  ),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(showTitles: true, reservedSize: 35),
                  ),
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                borderData: FlBorderData(show: true),
                barGroups: barGroups,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Attendance Tab (Donut Chart) ──

/// Displays a donut chart of attendance breakdown with rate summary and legend.
class _AttendanceTab extends StatelessWidget {
  final StudentProgress progress;
  final AppLocalizations t;
  final ThemeData theme;
  const _AttendanceTab({required this.progress, required this.t, required this.theme});

  @override
  Widget build(BuildContext context) {
    final ds = progress.attendanceOverview.datasets.isNotEmpty
        ? progress.attendanceOverview.datasets[0]
        : null;
    if (ds == null || ds.data.every((v) => v == 0)) {
      return Center(child: Text(t.t('progress.noData')));
    }

    final colors = [
      const Color(0xFF10b981),
      const Color(0xFFef4444),
      const Color(0xFF3b82f6),
      const Color(0xFFf59e0b),
    ];
    final sections = ds.data.asMap().entries.map((e) {
      return PieChartSectionData(
        value: e.value,
        color: colors[e.key % colors.length],
        title: '${e.value.toInt()}',
        radius: 55,
        titleStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.white),
      );
    }).toList();

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Text(t.t('progress.attendance'),
              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text(
            '${progress.attendanceSummary.attendanceRate.toStringAsFixed(1)}%',
            style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.bold),
          ),
          Text(
            '${progress.attendanceSummary.present}/${progress.attendanceSummary.total}',
            style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          Expanded(
            child: PieChart(
              PieChartData(
                sections: sections,
                centerSpaceRadius: 55,
                sectionsSpace: 2,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            children: progress.attendanceOverview.labels.asMap().entries.map((e) {
              return Row(mainAxisSize: MainAxisSize.min, children: [
                Container(width: 12, height: 12, color: colors[e.key % colors.length]),
                const SizedBox(width: 4),
                Text(e.value, style: const TextStyle(fontSize: 12)),
              ]);
            }).toList(),
          ),
        ],
      ),
    );
  }
}
