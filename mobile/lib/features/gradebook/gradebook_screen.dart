import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/gradebook.dart';
import 'package:ecole_platform/features/gradebook/gradebook_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

class GradebookScreen extends ConsumerStatefulWidget {
  const GradebookScreen({super.key});

  @override
  ConsumerState<GradebookScreen> createState() => _GradebookScreenState();
}

class _GradebookScreenState extends ConsumerState<GradebookScreen> {
  String? _selectedClassId;
  final Map<String, TextEditingController> _controllers = {};

  @override
  void dispose() {
    for (final controller in _controllers.values) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final classesAsync = ref.watch(gradebookClassesProvider);
    final saveState = ref.watch(gradeUpdateProvider);

    ref.listen<AsyncValue<void>>(gradeUpdateProvider, (previous, next) {
      next.whenOrNull(
        data: (_) {
          if (!mounted) {
            return;
          }
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(t.t('gradebook.saveSuccess'))),
          );
        },
        error: (error, _) {
          if (!mounted) {
            return;
          }
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(error.toString())),
          );
        },
      );
    });

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('gradebook.title')),
        actions: [
          IconButton(
            onPressed: _selectedClassId == null ? null : _exportGrades,
            icon: const Icon(Icons.download_outlined),
            tooltip: t.t('gradebook.export'),
          ),
          IconButton(
            onPressed: _selectedClassId == null || saveState.isLoading
                ? null
                : _saveGrades,
            icon: saveState.isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.save_outlined),
            tooltip: t.t('gradebook.save'),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.base),
        child: Column(
          children: [
            classesAsync.when(
              data: (classes) {
                _selectedClassId ??=
                    classes.isNotEmpty ? classes.first.id : null;
                return DropdownButtonFormField<String>(
                  initialValue: _selectedClassId,
                  decoration: InputDecoration(
                    labelText: t.t('gradebook.classLabel'),
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
                    if (value == null) {
                      return;
                    }
                    setState(() {
                      _selectedClassId = value;
                    });
                  },
                );
              },
              error: (error, _) => AppErrorWidget(
                message: error.toString(),
              ),
              loading: () => const AppSkeleton(
                variant: SkeletonVariant.line,
                height: 52,
              ),
            ),
            const SizedBox(height: AppSpacing.base),
            Expanded(
              child: _selectedClassId == null
                  ? AppEmptyState(
                      icon: Icons.class_outlined,
                      title: t.t('gradebook.noClasses'),
                    )
                  : _GradebookGridView(
                      classId: _selectedClassId!,
                      controllerFor: _controllerFor,
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _exportGrades() async {
    if (_selectedClassId == null) {
      return;
    }
    final t = AppLocalizations.of(ref);
    final url = await ref
        .read(gradebookRepositoryProvider)
        .exportGrades(_selectedClassId!, format: 'csv');
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          url == null
              ? t.t('gradebook.exportQueued')
              : '${t.t('gradebook.exportReady')}: $url',
        ),
      ),
    );
  }

  Future<void> _saveGrades() async {
    if (_selectedClassId == null) {
      return;
    }
    final grid = ref.read(gradebookProvider(_selectedClassId!)).valueOrNull;
    if (grid == null) {
      return;
    }

    final updates = <GradeValueUpdate>[];
    for (final entry in grid.entries) {
      for (final column in grid.columns) {
        final controller = _controllerFor(entry.studentId, column.assessmentId);
        final rawValue = controller.text.trim();
        if (rawValue.isEmpty) {
          continue;
        }
        final parsed = double.tryParse(rawValue.replaceAll(',', '.'));
        if (parsed == null || !_isValidGrade(parsed)) {
          continue;
        }
        updates.add(
          GradeValueUpdate(
            studentId: entry.studentId,
            assessmentId: column.assessmentId,
            value: parsed,
          ),
        );
      }
    }

    await ref.read(gradeUpdateProvider.notifier).save(
          BulkGradeUpdate(
            classId: _selectedClassId!,
            grades: updates,
          ),
        );
  }

  TextEditingController _controllerFor(
    String studentId,
    String assessmentId, [
    double? initialValue,
  ]) {
    final key = '$studentId::$assessmentId';
    return _controllers.putIfAbsent(
      key,
      () => TextEditingController(
        text: initialValue?.toStringAsFixed(1) ?? '',
      ),
    );
  }

  bool _isValidGrade(double value) {
    final normalized = (value * 2).roundToDouble() / 2;
    return value >= 0 && value <= 20 && normalized == value;
  }
}

class _GradebookGridView extends ConsumerWidget {
  final String classId;
  final TextEditingController Function(
    String studentId,
    String assessmentId,
    double? initialValue,
  ) controllerFor;

  const _GradebookGridView({
    required this.classId,
    required this.controllerFor,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(ref);
    final gradebookAsync = ref.watch(gradebookProvider(classId));

    return gradebookAsync.when(
      data: (grid) {
        if (grid.entries.isEmpty || grid.columns.isEmpty) {
          return AppEmptyState(
            icon: Icons.table_chart_outlined,
            title: t.t('gradebook.empty'),
          );
        }

        return SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            headingRowHeight: 64,
            columns: [
              DataColumn(label: Text(t.t('gradebook.student'))),
              ...grid.columns.map(
                (column) => DataColumn(
                  label: SizedBox(
                    width: 96,
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(column.title, overflow: TextOverflow.ellipsis),
                        Text(
                          '${column.weight.toStringAsFixed(1)}%',
                          style: Theme.of(context).textTheme.labelSmall,
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              DataColumn(label: Text(t.t('gradebook.average'))),
            ],
            rows: grid.entries
                .map(
                  (entry) => DataRow(
                    cells: [
                      DataCell(
                        InkWell(
                          onTap: () {
                            context.push('/gradebook/student/${entry.studentId}');
                          },
                          child: Text(entry.studentName),
                        ),
                      ),
                      ...grid.columns.map(
                        (column) => DataCell(
                          _GradeCell(
                            studentId: entry.studentId,
                            assessmentId: column.assessmentId,
                            controller: controllerFor(
                              entry.studentId,
                              column.assessmentId,
                              entry.grades[column.assessmentId],
                            ),
                          ),
                        ),
                      ),
                      DataCell(
                        AppBadge(
                          label: entry.weightedAverage.toStringAsFixed(1),
                          variant: entry.weightedAverage >= 10
                              ? AppBadgeVariant.success
                              : AppBadgeVariant.error,
                        ),
                      ),
                    ],
                  ),
                )
                .toList(),
          ),
        );
      },
      error: (error, _) => AppErrorWidget(
        message: error.toString(),
        onRetry: () => ref.read(gradebookProvider(classId).notifier).refresh(),
      ),
      loading: () => const AppSkeleton(
        variant: SkeletonVariant.tableRow,
        count: 6,
      ),
    );
  }
}

class _GradeCell extends StatefulWidget {
  final String studentId;
  final String assessmentId;
  final TextEditingController controller;

  const _GradeCell({
    required this.studentId,
    required this.assessmentId,
    required this.controller,
  });

  @override
  State<_GradeCell> createState() => _GradeCellState();
}

class _GradeCellState extends State<_GradeCell> {
  @override
  Widget build(BuildContext context) {
    final parsed =
        double.tryParse(widget.controller.text.replaceAll(',', '.'));
    final theme = Theme.of(context);
    final fillColor = parsed == null
        ? theme.colorScheme.surfaceContainerHighest
        : parsed >= 10
            ? theme.colorScheme.primaryContainer
            : theme.colorScheme.errorContainer;

    return SizedBox(
      width: 72,
      child: TextFormField(
        controller: widget.controller,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        textAlign: TextAlign.center,
        decoration: InputDecoration(
          isDense: true,
          filled: true,
          fillColor: fillColor,
          contentPadding: const EdgeInsets.symmetric(vertical: 10),
        ),
        onChanged: (_) => setState(() {}),
      ),
    );
  }
}
