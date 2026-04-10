import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/rubric.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'rubrics_provider.dart';

class RubricsListScreen extends ConsumerStatefulWidget {
  const RubricsListScreen({super.key});

  @override
  ConsumerState<RubricsListScreen> createState() => _RubricsListScreenState();
}

class _RubricsListScreenState extends ConsumerState<RubricsListScreen> {
  bool _creating = false;

  List<RubricCriterion> _defaultCriteria() {
    return const [
      RubricCriterion(
        id: 'knowledge',
        name: 'Knowledge',
        weight: 40,
        levels: [
          RubricLevel(
            id: 'knowledge-foundation',
            label: 'Foundation',
            score: 10,
            description: 'Shows partial understanding',
          ),
          RubricLevel(
            id: 'knowledge-proficient',
            label: 'Proficient',
            score: 15,
            description: 'Meets expectations',
          ),
          RubricLevel(
            id: 'knowledge-advanced',
            label: 'Advanced',
            score: 20,
            description: 'Exceeds expectations',
          ),
        ],
      ),
      RubricCriterion(
        id: 'application',
        name: 'Application',
        weight: 60,
        levels: [
          RubricLevel(
            id: 'application-foundation',
            label: 'Foundation',
            score: 12,
            description: 'Needs support to apply concepts',
          ),
          RubricLevel(
            id: 'application-proficient',
            label: 'Proficient',
            score: 18,
            description: 'Applies concepts correctly',
          ),
          RubricLevel(
            id: 'application-advanced',
            label: 'Advanced',
            score: 24,
            description: 'Applies concepts with depth',
          ),
        ],
      ),
    ];
  }

  Future<void> _createRubric() async {
    final titleController = TextEditingController();
    final subjectController = TextEditingController();
    final descriptionController = TextEditingController();

    final shouldCreate = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Create rubric'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: titleController,
              decoration: const InputDecoration(labelText: 'Title'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: subjectController,
              decoration: const InputDecoration(labelText: 'Subject'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: descriptionController,
              maxLines: 3,
              decoration: const InputDecoration(labelText: 'Description'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(AppLocalizations.of(ref).t('common.cancel')),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Create'),
          ),
        ],
      ),
    );

    if (shouldCreate != true) {
      titleController.dispose();
      subjectController.dispose();
      descriptionController.dispose();
      return;
    }

    setState(() => _creating = true);
    try {
      final rubric = await ref.read(rubricRepositoryProvider).createRubric(
            title: titleController.text.trim(),
            subject: subjectController.text.trim(),
            description: descriptionController.text.trim(),
            criteria: _defaultCriteria(),
          );
      ref.invalidate(rubricsProvider);
      if (!mounted) return;
      context.push('/rubrics/${rubric.id}/edit');
    } finally {
      setState(() => _creating = false);
      titleController.dispose();
      subjectController.dispose();
      descriptionController.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    final rubricsAsync = ref.watch(rubricsProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('rubrics.title'))),
      body: rubricsAsync.when(
        data: (rubrics) {
          if (rubrics.isEmpty) {
            return const AppEmptyState(
              icon: Icons.fact_check_outlined,
              title: 'No rubrics configured',
            );
          }
          return RefreshIndicator(
            onRefresh: () async => ref.invalidate(rubricsProvider),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: rubrics.length,
              itemBuilder: (context, index) {
                final rubric = rubrics[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                rubric.title,
                                style: Theme.of(context)
                                    .textTheme
                                    .titleMedium
                                    ?.copyWith(fontWeight: FontWeight.w700),
                              ),
                            ),
                            AppBadge(label: rubric.subject ?? 'General'),
                          ],
                        ),
                        if (rubric.description != null &&
                            rubric.description!.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          Text(rubric.description!),
                        ],
                        const SizedBox(height: 8),
                        Text(
                          '${rubric.criteria.length} criteria · ${rubric.maxScore.toStringAsFixed(0)} pts',
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            FilledButton.tonal(
                              onPressed: () => context.push('/rubrics/${rubric.id}/edit'),
                              child: Text(t.t('rubrics.editor')),
                            ),
                            const SizedBox(width: 8),
                            FilledButton.tonal(
                              onPressed: () => context.push('/rubrics/${rubric.id}/grade'),
                              child: Text(t.t('rubrics.grade')),
                            ),
                            const Spacer(),
                            IconButton(
                              onPressed: () async {
                                await ref
                                    .read(rubricRepositoryProvider)
                                    .duplicateRubric(rubric.id);
                                ref.invalidate(rubricsProvider);
                              },
                              icon: const Icon(Icons.copy_outlined),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _creating ? null : _createRubric,
        icon: _creating
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.add_outlined),
        label: const Text('Create'),
      ),
    );
  }
}
