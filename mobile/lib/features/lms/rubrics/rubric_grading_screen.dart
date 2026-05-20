import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/lms/rubric.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'rubrics_provider.dart';

class RubricGradingScreen extends ConsumerStatefulWidget {
  final String rubricId;

  const RubricGradingScreen({
    super.key,
    required this.rubricId,
  });

  @override
  ConsumerState<RubricGradingScreen> createState() =>
      _RubricGradingScreenState();
}

class _RubricGradingScreenState extends ConsumerState<RubricGradingScreen> {
  final _studentController = TextEditingController();
  final _assignmentController = TextEditingController();
  final Map<String, String> _selectedLevels = {};
  RubricGradeResult? _result;
  bool _grading = false;

  @override
  void dispose() {
    _studentController.dispose();
    _assignmentController.dispose();
    super.dispose();
  }

  Future<void> _grade(Rubric rubric) async {
    setState(() => _grading = true);
    try {
      final entries = rubric.criteria.map((criterion) {
        final levelId =
            _selectedLevels[criterion.id] ?? criterion.levels.first.id;
        final level =
            criterion.levels.firstWhere((candidate) => candidate.id == levelId);
        return RubricGradeEntry(
          studentId: _studentController.text.trim(),
          criterionId: criterion.id,
          levelId: level.id,
          score: level.score,
        );
      }).toList();
      final result = await ref.read(rubricRepositoryProvider).gradeRubric(
            rubricId: rubric.id,
            assignmentId: _assignmentController.text.trim().isEmpty
                ? null
                : _assignmentController.text.trim(),
            entries: entries,
          );
      ref.invalidate(rubricResultsProvider(rubric.id));
      setState(() => _result = result);
    } finally {
      if (mounted) {
        setState(() => _grading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final rubricAsync = ref.watch(rubricProvider(widget.rubricId));
    final resultsAsync = ref.watch(rubricResultsProvider(widget.rubricId));
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('rubrics.grade'))),
      body: rubricAsync.when(
        data: (rubric) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextField(
              controller: _studentController,
              decoration: const InputDecoration(labelText: 'Student ID'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _assignmentController,
              decoration: const InputDecoration(
                labelText: 'Assignment ID (optional)',
              ),
            ),
            const SizedBox(height: 16),
            ...rubric.criteria.map(
              (criterion) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: DropdownButtonFormField<String>(
                  initialValue: _selectedLevels[criterion.id] ??
                      criterion.levels.firstOrNull?.id,
                  decoration: InputDecoration(labelText: criterion.name),
                  items: criterion.levels
                      .map(
                        (level) => DropdownMenuItem(
                          value: level.id,
                          child: Text(
                            '${level.label} · ${level.score.toStringAsFixed(0)} pts',
                          ),
                        ),
                      )
                      .toList(),
                  onChanged: (value) {
                    if (value != null) {
                      setState(() => _selectedLevels[criterion.id] = value);
                    }
                  },
                ),
              ),
            ),
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed: _grading ? null : () => _grade(rubric),
              icon: _grading
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.grading_outlined),
              label: Text(t.t('rubrics.grade')),
            ),
            if (_result != null) ...[
              const SizedBox(height: 24),
              AppStatCard(
                label: 'Latest grade',
                value:
                    '${_result!.totalScore.toStringAsFixed(1)} / ${_result!.maxScore.toStringAsFixed(1)}',
                icon: Icons.score_outlined,
              ),
            ],
            const SizedBox(height: 24),
            Text(
              'Rubric results',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: 12),
            resultsAsync.when(
              data: (results) {
                if (results.results.isEmpty) {
                  return const AppEmptyState(
                    icon: Icons.inbox_outlined,
                    title: 'No rubric grades yet',
                  );
                }
                return Column(
                  children: results.results
                      .map(
                        (item) => Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          child: ListTile(
                            title: Text(item.studentId),
                            subtitle: Text(
                              '${item.totalScore.toStringAsFixed(1)} / ${item.maxScore.toStringAsFixed(1)}',
                            ),
                            trailing: AppBadge(
                              label: '${item.percentage.toStringAsFixed(0)}%',
                              variant: AppBadgeVariant.info,
                            ),
                          ),
                        ),
                      )
                      .toList(),
                );
              },
              loading: () => const Padding(
                padding: EdgeInsets.all(16),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, _) => AppErrorWidget(message: error.toString()),
            ),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}
