import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/domain/entities/attendance.dart';
import 'package:ecole_platform/domain/entities/teacher.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'attendance_provider.dart';

class AttendanceHistoryScreen extends ConsumerStatefulWidget {
  final String? initialStudentId;
  final String? initialClassId;

  const AttendanceHistoryScreen({
    super.key,
    this.initialStudentId,
    this.initialClassId,
  });

  @override
  ConsumerState<AttendanceHistoryScreen> createState() =>
      _AttendanceHistoryScreenState();
}

class _AttendanceHistoryScreenState
    extends ConsumerState<AttendanceHistoryScreen> {
  String? _selectedClassId;
  String? _selectedStudentId;

  @override
  void initState() {
    super.initState();
    _selectedClassId = widget.initialClassId;
    _selectedStudentId = widget.initialStudentId;
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final classesAsync = ref.watch(attendanceClassesProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('attendance.history')),
      ),
      body: classesAsync.when(
        data: (classes) {
          _selectedClassId ??= classes.isNotEmpty ? classes.first.id : null;
          final studentsAsync = _selectedClassId == null
              ? AsyncValue<List<StudentInfo>>.data(const [])
              : ref.watch(attendanceStudentsProvider(_selectedClassId!));
          return studentsAsync.when(
            data: (students) {
              if (_selectedStudentId == null && students.isNotEmpty) {
                _selectedStudentId = students.first.id;
              }
              final historyAsync = _selectedStudentId == null
                  ? AsyncValue<List<AttendanceEntry>>.data(const [])
                  : ref.watch(attendanceHistoryProvider(_selectedStudentId!));
              return RefreshIndicator(
                onRefresh: () async {
                  if (_selectedStudentId != null) {
                    ref.invalidate(
                        attendanceHistoryProvider(_selectedStudentId!));
                  }
                },
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    _HistoryFilters(
                      classId: _selectedClassId,
                      studentId: _selectedStudentId,
                      classes: classes,
                      students: students,
                      onClassChanged: (value) {
                        setState(() {
                          _selectedClassId = value;
                          _selectedStudentId = null;
                        });
                      },
                      onStudentChanged: (value) {
                        setState(() {
                          _selectedStudentId = value;
                        });
                      },
                    ),
                    const SizedBox(height: 16),
                    historyAsync.when(
                      data: (history) => _HistoryContent(records: history),
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
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}

class _HistoryFilters extends StatelessWidget {
  final String? classId;
  final String? studentId;
  final List<ClassInfo> classes;
  final List<StudentInfo> students;
  final ValueChanged<String?> onClassChanged;
  final ValueChanged<String?> onStudentChanged;

  const _HistoryFilters({
    required this.classId,
    required this.studentId,
    required this.classes,
    required this.students,
    required this.onClassChanged,
    required this.onStudentChanged,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Attendance history',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: classId,
              decoration: const InputDecoration(
                labelText: 'Class',
                border: OutlineInputBorder(),
              ),
              items: classes
                  .map<DropdownMenuItem<String>>(
                    (item) => DropdownMenuItem<String>(
                      value: item.id,
                      child: Text(item.name),
                    ),
                  )
                  .toList(),
              onChanged: onClassChanged,
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: studentId,
              decoration: const InputDecoration(
                labelText: 'Student',
                border: OutlineInputBorder(),
              ),
              items: students
                  .map<DropdownMenuItem<String>>(
                    (item) => DropdownMenuItem<String>(
                      value: item.id,
                      child: Text(item.fullName),
                    ),
                  )
                  .toList(),
              onChanged: onStudentChanged,
            ),
          ],
        ),
      ),
    );
  }
}

class _HistoryContent extends StatelessWidget {
  final List<AttendanceEntry> records;

  const _HistoryContent({required this.records});

  @override
  Widget build(BuildContext context) {
    if (records.isEmpty) {
      return const AppEmptyState(
        icon: Icons.event_busy,
        title: 'No attendance history yet',
      );
    }

    final presentCount =
        records.where((record) => record.status == 'present').length;
    final absentCount =
        records.where((record) => record.status == 'absent').length;
    final lateCount = records.where((record) => record.status == 'late').length;
    final excusedCount =
        records.where((record) => record.status == 'excused').length;
    final attendanceRate =
        records.isEmpty ? 0.0 : (presentCount / records.length) * 100;

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
                value: '${attendanceRate.toStringAsFixed(1)}%',
                icon: Icons.percent,
              ),
            ),
            SizedBox(
              width: 160,
              child: AppStatCard(
                label: 'Present',
                value: '$presentCount',
                icon: Icons.check_circle_outline,
              ),
            ),
            SizedBox(
              width: 160,
              child: AppStatCard(
                label: 'Absent',
                value: '$absentCount',
                icon: Icons.cancel_outlined,
              ),
            ),
            SizedBox(
              width: 160,
              child: AppStatCard(
                label: 'Late / Excused',
                value: '${lateCount + excusedCount}',
                icon: Icons.schedule,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        _AttendanceHeatmap(records: records),
        const SizedBox(height: 20),
        Text(
          'Recent sessions',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: 12),
        ...records.take(12).map((record) => _HistoryRow(record: record)),
      ],
    );
  }
}

class _AttendanceHeatmap extends StatelessWidget {
  final List<AttendanceEntry> records;

  const _AttendanceHeatmap({required this.records});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final now = DateTime.now();
    final start = now.subtract(const Duration(days: 34));
    final recordByDay = <String, AttendanceEntry>{};

    for (final record in records) {
      final dayKey = _dayKey(DateTime.tryParse(record.date) ?? now);
      recordByDay[dayKey] = record;
    }

    final days = List.generate(35, (index) {
      return DateTime(start.year, start.month, start.day + index);
    });

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Calendar heatmap',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 12),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 7,
                mainAxisSpacing: 8,
                crossAxisSpacing: 8,
                childAspectRatio: 1,
              ),
              itemCount: days.length,
              itemBuilder: (context, index) {
                final day = days[index];
                final record = recordByDay[_dayKey(day)];
                return Tooltip(
                  message: DateFormat.yMMMd().format(day),
                  child: Container(
                    decoration: BoxDecoration(
                      color: _statusColor(theme, record?.status),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: theme.colorScheme.outlineVariant,
                      ),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      '${day.day}',
                      style: theme.textTheme.labelMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Color _statusColor(ThemeData theme, String? status) {
    return switch (status) {
      'present' => theme.colorScheme.primaryContainer,
      'absent' => theme.colorScheme.errorContainer,
      'late' => theme.colorScheme.secondaryContainer,
      'excused' => theme.colorScheme.tertiaryContainer,
      _ => theme.colorScheme.surfaceContainerHighest,
    };
  }

  String _dayKey(DateTime date) => DateFormat('yyyy-MM-dd').format(date);
}

class _HistoryRow extends StatelessWidget {
  final AttendanceEntry record;

  const _HistoryRow({required this.record});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: _statusColor(theme, record.status),
          child: Icon(
            record.status == 'present' ? Icons.check : Icons.remove,
            color: theme.colorScheme.onPrimaryContainer,
          ),
        ),
        title: Text(DateFormat.yMMMd().format(DateTime.parse(record.date))),
        subtitle: Text(
          [
            record.status,
            if (record.slot != null) record.slot,
            if (record.absenceReason != null) record.absenceReason,
          ].whereType<String>().join(' • '),
        ),
        trailing: AppBadge(
          label: record.status,
          variant: switch (record.status) {
            'present' => AppBadgeVariant.success,
            'absent' => AppBadgeVariant.error,
            'late' => AppBadgeVariant.warning,
            'excused' => AppBadgeVariant.info,
            _ => AppBadgeVariant.neutral,
          },
        ),
      ),
    );
  }

  Color _statusColor(ThemeData theme, String status) {
    return switch (status) {
      'present' => theme.colorScheme.primaryContainer,
      'absent' => theme.colorScheme.errorContainer,
      'late' => theme.colorScheme.secondaryContainer,
      'excused' => theme.colorScheme.tertiaryContainer,
      _ => theme.colorScheme.surfaceContainerHighest,
    };
  }
}
