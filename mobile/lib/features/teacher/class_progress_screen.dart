/// Teacher-facing class progress dashboard.
///
/// Phase I (Web/Mobile parity) — I10.
///
/// Mirrors `web/src/features/teacher/ClassProgressPage.tsx`:
///   * Class picker (from /teacher/classes).
///   * Summary stat cards (grade avg / attendance / content / student count).
///   * Bar chart — per-student grade comparison.
///   * Pie chart — content completion tiers (0–25 / 25–50 / 50–75 / 75–100 %).
///   * Bar chart — per-student attendance rate.
///   * Ranked student list; tap → `/progress/{studentId}`.
library;

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/domain/entities/teacher.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'class_progress_provider.dart';

enum _StudentSort { name, grade, attendance, content }

class ClassProgressScreen extends ConsumerStatefulWidget {
  const ClassProgressScreen({super.key});

  @override
  ConsumerState<ClassProgressScreen> createState() =>
      _ClassProgressScreenState();
}

class _ClassProgressScreenState extends ConsumerState<ClassProgressScreen> {
  String? _selectedClassId;
  _StudentSort _sort = _StudentSort.grade;
  bool _sortAscending = false;

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final classesAsync = ref.watch(teacherClassesListProvider);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('classProgress.title'))),
      body: classesAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(
          message: error.toString(),
          onRetry: () => ref.invalidate(teacherClassesListProvider),
        ),
        data: (classes) {
          if (classes.isEmpty) {
            return AppEmptyState(
              icon: Icons.class_outlined,
              title: t.t('classProgress.noClasses'),
              subtitle: t.t('classProgress.noClassesSubtitle'),
            );
          }
          _selectedClassId ??= classes.first.id;
          return _ClassProgressBody(
            t: t,
            classes: classes,
            selectedClassId: _selectedClassId!,
            sort: _sort,
            ascending: _sortAscending,
            onClassChanged: (id) => setState(() => _selectedClassId = id),
            onSortChanged: (key) => setState(() {
              if (_sort == key) {
                _sortAscending = !_sortAscending;
              } else {
                _sort = key;
                _sortAscending = key == _StudentSort.name;
              }
            }),
          );
        },
      ),
    );
  }
}

class _ClassProgressBody extends ConsumerWidget {
  final AppLocalizations t;
  final List<ClassInfo> classes;
  final String selectedClassId;
  final _StudentSort sort;
  final bool ascending;
  final ValueChanged<String> onClassChanged;
  final ValueChanged<_StudentSort> onSortChanged;

  const _ClassProgressBody({
    required this.t,
    required this.classes,
    required this.selectedClassId,
    required this.sort,
    required this.ascending,
    required this.onClassChanged,
    required this.onSortChanged,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final progressAsync = ref.watch(classProgressProvider(selectedClassId));

    return RefreshIndicator(
      onRefresh: () async {
        ref.invalidate(teacherClassesListProvider);
        ref.invalidate(classProgressProvider(selectedClassId));
        await ref.read(classProgressProvider(selectedClassId).future);
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _ClassPicker(
            t: t,
            classes: classes,
            selectedClassId: selectedClassId,
            onChanged: onClassChanged,
          ),
          const SizedBox(height: 16),
          progressAsync.when(
            loading: () => const Padding(
              padding: EdgeInsets.symmetric(vertical: 48),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (error, _) => AppErrorWidget(
              message: error.toString(),
              onRetry: () =>
                  ref.invalidate(classProgressProvider(selectedClassId)),
            ),
            data: (data) => _DashboardContent(
              data: data,
              t: t,
              sort: sort,
              ascending: ascending,
              onSortChanged: onSortChanged,
              onStudentTap: (studentId) =>
                  context.push('/progress/$studentId'),
            ),
          ),
        ],
      ),
    );
  }
}

class _ClassPicker extends StatelessWidget {
  final AppLocalizations t;
  final List<ClassInfo> classes;
  final String selectedClassId;
  final ValueChanged<String> onChanged;

  const _ClassPicker({
    required this.t,
    required this.classes,
    required this.selectedClassId,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: DropdownButtonFormField<String>(
          initialValue: selectedClassId,
          decoration: InputDecoration(
            labelText: t.t('classProgress.selectClass'),
            border: const OutlineInputBorder(),
            isDense: true,
          ),
          items: classes
              .map(
                (c) => DropdownMenuItem(
                  value: c.id,
                  child: Text('${c.name} (${c.code})'),
                ),
              )
              .toList(growable: false),
          onChanged: (value) {
            if (value != null) onChanged(value);
          },
        ),
      ),
    );
  }
}

class _DashboardContent extends StatelessWidget {
  final ClassProgressData data;
  final AppLocalizations t;
  final _StudentSort sort;
  final bool ascending;
  final ValueChanged<_StudentSort> onSortChanged;
  final ValueChanged<String> onStudentTap;

  const _DashboardContent({
    required this.data,
    required this.t,
    required this.sort,
    required this.ascending,
    required this.onSortChanged,
    required this.onStudentTap,
  });

  @override
  Widget build(BuildContext context) {
    final averages = data.classAverages;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          data.className,
          style: Theme.of(context).textTheme.titleLarge
              ?.copyWith(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            SizedBox(
              width: 170,
              child: AppStatCard(
                label: t.t('classProgress.classGradeAvg'),
                value: averages.gradeAverage != null
                    ? averages.gradeAverage!.toStringAsFixed(1)
                    : '—',
                icon: Icons.grade_outlined,
              ),
            ),
            SizedBox(
              width: 170,
              child: AppStatCard(
                label: t.t('classProgress.classAttendance'),
                value: averages.attendanceRate != null
                    ? '${averages.attendanceRate!.toStringAsFixed(0)}%'
                    : '—',
                icon: Icons.event_available_outlined,
              ),
            ),
            SizedBox(
              width: 170,
              child: AppStatCard(
                label: t.t('classProgress.classContent'),
                value: averages.contentCompletionRate != null
                    ? '${averages.contentCompletionRate!.toStringAsFixed(0)}%'
                    : '—',
                icon: Icons.auto_stories_outlined,
              ),
            ),
            SizedBox(
              width: 170,
              child: AppStatCard(
                label: t.t('classProgress.studentCount'),
                value: '${data.studentCount}',
                icon: Icons.groups_outlined,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        if (data.students.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 32),
            child: AppEmptyState(
              icon: Icons.people_outline,
              title: t.t('classProgress.noStudents'),
            ),
          )
        else ...[
          _GradeComparisonChart(
            title: t.t('classProgress.gradeComparison'),
            series: data.gradeComparison,
            maxY: 100,
          ),
          const SizedBox(height: 16),
          _ContentCompletionPie(students: data.students, t: t),
          const SizedBox(height: 16),
          _GradeComparisonChart(
            title: t.t('classProgress.attendanceComparison'),
            series: data.attendanceComparison,
            maxY: 100,
            barColor: Colors.green.shade600,
          ),
          const SizedBox(height: 16),
          _StudentListCard(
            students: data.students,
            t: t,
            sort: sort,
            ascending: ascending,
            onSortChanged: onSortChanged,
            onStudentTap: onStudentTap,
          ),
        ],
      ],
    );
  }
}

class _GradeComparisonChart extends StatelessWidget {
  final String title;
  final ChartSeries series;
  final double maxY;
  final Color? barColor;

  const _GradeComparisonChart({
    required this.title,
    required this.series,
    required this.maxY,
    this.barColor,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (series.labels.isEmpty) {
      return const SizedBox.shrink();
    }
    final color = barColor ?? theme.colorScheme.primary;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 220,
              child: BarChart(
                BarChartData(
                  maxY: maxY,
                  barGroups: [
                    for (var i = 0; i < series.values.length; i += 1)
                      BarChartGroupData(
                        x: i,
                        barRods: [
                          BarChartRodData(
                            toY: series.values[i] ?? 0,
                            color: color,
                            width: 18,
                            borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(4),
                            ),
                          ),
                        ],
                      ),
                  ],
                  titlesData: FlTitlesData(
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 46,
                        getTitlesWidget: (value, meta) {
                          final idx = value.toInt();
                          if (idx < 0 || idx >= series.labels.length) {
                            return const SizedBox.shrink();
                          }
                          final label = series.labels[idx];
                          final short = label.length > 8
                              ? '${label.substring(0, 7)}…'
                              : label;
                          return Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Transform.rotate(
                              angle: -0.5,
                              child: Text(
                                short,
                                style: theme.textTheme.labelSmall,
                              ),
                            ),
                          );
                        },
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 34,
                        interval: maxY / 4,
                        getTitlesWidget: (value, meta) => Text(
                          value.toStringAsFixed(0),
                          style: theme.textTheme.labelSmall,
                        ),
                      ),
                    ),
                  ),
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: maxY / 4,
                    getDrawingHorizontalLine: (_) => FlLine(
                      color: theme.colorScheme.outlineVariant,
                      strokeWidth: 1,
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ContentCompletionPie extends StatelessWidget {
  final List<StudentProgressRow> students;
  final AppLocalizations t;

  const _ContentCompletionPie({required this.students, required this.t});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final buckets = _bucketize(students);
    final total = buckets.values.fold<int>(0, (a, b) => a + b);
    if (total == 0) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                t.t('classProgress.contentCompletion'),
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 12),
              AppEmptyState(
                icon: Icons.pie_chart_outline,
                title: t.t('classProgress.noContentData'),
              ),
            ],
          ),
        ),
      );
    }

    final tiers = <_Tier>[
      _Tier(
        label: t.t('classProgress.tier.low'),
        count: buckets['low']!,
        color: Colors.red.shade400,
      ),
      _Tier(
        label: t.t('classProgress.tier.fair'),
        count: buckets['fair']!,
        color: Colors.orange.shade400,
      ),
      _Tier(
        label: t.t('classProgress.tier.good'),
        count: buckets['good']!,
        color: Colors.lightGreen.shade500,
      ),
      _Tier(
        label: t.t('classProgress.tier.excellent'),
        count: buckets['excellent']!,
        color: Colors.green.shade700,
      ),
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              t.t('classProgress.contentCompletion'),
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 180,
              child: Row(
                children: [
                  Expanded(
                    child: PieChart(
                      PieChartData(
                        sectionsSpace: 2,
                        centerSpaceRadius: 32,
                        sections: [
                          for (final tier in tiers)
                            if (tier.count > 0)
                              PieChartSectionData(
                                color: tier.color,
                                value: tier.count.toDouble(),
                                title: '${tier.count}',
                                radius: 54,
                                titleStyle: const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w700,
                                  fontSize: 12,
                                ),
                              ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        for (final tier in tiers)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 2),
                            child: Row(
                              children: [
                                Container(
                                  width: 12,
                                  height: 12,
                                  decoration: BoxDecoration(
                                    color: tier.color,
                                    borderRadius: BorderRadius.circular(2),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    tier.label,
                                    style: theme.textTheme.bodySmall,
                                  ),
                                ),
                                Text(
                                  '${tier.count}',
                                  style: theme.textTheme.labelMedium
                                      ?.copyWith(fontWeight: FontWeight.w700),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Map<String, int> _bucketize(List<StudentProgressRow> students) {
    var low = 0;
    var fair = 0;
    var good = 0;
    var excellent = 0;
    for (final s in students) {
      final rate = s.contentCompletionRate;
      if (rate == null) continue;
      if (rate < 25) {
        low += 1;
      } else if (rate < 50) {
        fair += 1;
      } else if (rate < 75) {
        good += 1;
      } else {
        excellent += 1;
      }
    }
    return {'low': low, 'fair': fair, 'good': good, 'excellent': excellent};
  }
}

class _Tier {
  final String label;
  final int count;
  final Color color;
  const _Tier({required this.label, required this.count, required this.color});
}

class _StudentListCard extends StatelessWidget {
  final List<StudentProgressRow> students;
  final AppLocalizations t;
  final _StudentSort sort;
  final bool ascending;
  final ValueChanged<_StudentSort> onSortChanged;
  final ValueChanged<String> onStudentTap;

  const _StudentListCard({
    required this.students,
    required this.t,
    required this.sort,
    required this.ascending,
    required this.onSortChanged,
    required this.onStudentTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sorted = [...students];
    sorted.sort((a, b) {
      int cmp;
      switch (sort) {
        case _StudentSort.name:
          cmp = a.studentName.toLowerCase().compareTo(
                b.studentName.toLowerCase(),
              );
          break;
        case _StudentSort.grade:
          cmp = (a.gradeAverage ?? -1).compareTo(b.gradeAverage ?? -1);
          break;
        case _StudentSort.attendance:
          cmp = (a.attendanceRate ?? -1).compareTo(b.attendanceRate ?? -1);
          break;
        case _StudentSort.content:
          cmp = (a.contentCompletionRate ?? -1)
              .compareTo(b.contentCompletionRate ?? -1);
          break;
      }
      return ascending ? cmp : -cmp;
    });

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              t.t('classProgress.perStudent'),
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: [
                _SortChip(
                  label: t.t('classProgress.sort.name'),
                  active: sort == _StudentSort.name,
                  ascending: ascending,
                  onTap: () => onSortChanged(_StudentSort.name),
                ),
                _SortChip(
                  label: t.t('classProgress.sort.grade'),
                  active: sort == _StudentSort.grade,
                  ascending: ascending,
                  onTap: () => onSortChanged(_StudentSort.grade),
                ),
                _SortChip(
                  label: t.t('classProgress.sort.attendance'),
                  active: sort == _StudentSort.attendance,
                  ascending: ascending,
                  onTap: () => onSortChanged(_StudentSort.attendance),
                ),
                _SortChip(
                  label: t.t('classProgress.sort.content'),
                  active: sort == _StudentSort.content,
                  ascending: ascending,
                  onTap: () => onSortChanged(_StudentSort.content),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ...sorted.map(
              (student) => _StudentTile(
                student: student,
                onTap: () => onStudentTap(student.studentId),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SortChip extends StatelessWidget {
  final String label;
  final bool active;
  final bool ascending;
  final VoidCallback onTap;

  const _SortChip({
    required this.label,
    required this.active,
    required this.ascending,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label),
          if (active) ...[
            const SizedBox(width: 4),
            Icon(
              ascending ? Icons.arrow_upward : Icons.arrow_downward,
              size: 14,
            ),
          ],
        ],
      ),
      selected: active,
      onSelected: (_) => onTap(),
    );
  }
}

class _StudentTile extends StatelessWidget {
  final StudentProgressRow student;
  final VoidCallback onTap;

  const _StudentTile({required this.student, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(6),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
        child: Row(
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: theme.colorScheme.primaryContainer,
              child: Text(
                _initials(student.studentName),
                style: TextStyle(
                  color: theme.colorScheme.onPrimaryContainer,
                  fontWeight: FontWeight.w700,
                  fontSize: 12,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    student.studentName,
                    style: theme.textTheme.bodyLarge
                        ?.copyWith(fontWeight: FontWeight.w600),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    _metricLine(student),
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ),
            ),
            Text(
              student.gradeAverage != null
                  ? student.gradeAverage!.toStringAsFixed(1)
                  : '—',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w700,
                color: _gradeColor(student.gradeAverage, theme),
              ),
            ),
            const Icon(Icons.chevron_right, size: 18),
          ],
        ),
      ),
    );
  }

  String _metricLine(StudentProgressRow s) {
    final att = s.attendanceRate != null
        ? '${s.attendanceRate!.toStringAsFixed(0)}%'
        : '—';
    final content = s.contentCompletionRate != null
        ? '${s.contentCompletionRate!.toStringAsFixed(0)}%'
        : '—';
    return '📅 $att   📚 $content';
  }

  String _initials(String name) {
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.isEmpty || parts.first.isEmpty) return '?';
    if (parts.length == 1) return parts.first.characters.first.toUpperCase();
    return (parts.first.characters.first + parts.last.characters.first)
        .toUpperCase();
  }

  Color _gradeColor(double? grade, ThemeData theme) {
    if (grade == null) return theme.colorScheme.outline;
    if (grade >= 80) return Colors.green.shade600;
    if (grade >= 50) return Colors.orange.shade700;
    return theme.colorScheme.error;
  }
}
