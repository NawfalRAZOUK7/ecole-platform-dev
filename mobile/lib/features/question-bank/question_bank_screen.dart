import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'question_bank_provider.dart';

class QuestionBankScreen extends ConsumerStatefulWidget {
  const QuestionBankScreen({super.key});

  @override
  ConsumerState<QuestionBankScreen> createState() => _QuestionBankScreenState();
}

class _QuestionBankScreenState extends ConsumerState<QuestionBankScreen> {
  bool _creating = false;

  Future<void> _createQuestion() async {
    final subjectController = TextEditingController();
    final textController = TextEditingController();
    final answerController = TextEditingController();
    final tagsController = TextEditingController();
    String type = 'mcq';
    String difficulty = 'medium';

    final shouldCreate = await showDialog<bool>(
      context: context,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setStateDialog) => AlertDialog(
            title: const Text('Create question'),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: subjectController,
                    decoration: const InputDecoration(labelText: 'Subject'),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: type,
                    decoration: const InputDecoration(labelText: 'Type'),
                    items: const [
                      DropdownMenuItem(value: 'mcq', child: Text('MCQ')),
                      DropdownMenuItem(
                        value: 'true_false',
                        child: Text('True / False'),
                      ),
                      DropdownMenuItem(
                        value: 'short_answer',
                        child: Text('Short answer'),
                      ),
                      DropdownMenuItem(value: 'essay', child: Text('Essay')),
                    ],
                    onChanged: (value) {
                      if (value != null) {
                        setStateDialog(() => type = value);
                      }
                    },
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: difficulty,
                    decoration: const InputDecoration(labelText: 'Difficulty'),
                    items: const [
                      DropdownMenuItem(value: 'easy', child: Text('Easy')),
                      DropdownMenuItem(value: 'medium', child: Text('Medium')),
                      DropdownMenuItem(value: 'hard', child: Text('Hard')),
                    ],
                    onChanged: (value) {
                      if (value != null) {
                        setStateDialog(() => difficulty = value);
                      }
                    },
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: textController,
                    maxLines: 4,
                    decoration: const InputDecoration(labelText: 'Question text'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: answerController,
                    decoration:
                        const InputDecoration(labelText: 'Correct answer'),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: tagsController,
                    decoration: const InputDecoration(
                      labelText: 'Tags (comma separated)',
                    ),
                  ),
                ],
              ),
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
      },
    );

    if (shouldCreate != true) {
      subjectController.dispose();
      textController.dispose();
      answerController.dispose();
      tagsController.dispose();
      return;
    }

    setState(() => _creating = true);
    try {
      await ref.read(questionBankRepositoryProvider).createQuestion(
            subject: subjectController.text.trim(),
            type: type,
            difficulty: difficulty,
            text: textController.text.trim(),
            correctAnswer: answerController.text.trim().isEmpty
                ? null
                : answerController.text.trim(),
            tags: tagsController.text
                .split(',')
                .map((item) => item.trim())
                .where((item) => item.isNotEmpty)
                .toList(),
          );
      ref.invalidate(questionBankQuestionsProvider);
      ref.invalidate(questionBankStatsProvider);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Question created')),
      );
    } finally {
      setState(() => _creating = false);
      subjectController.dispose();
      textController.dispose();
      answerController.dispose();
      tagsController.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    final questionsAsync = ref.watch(questionBankQuestionsProvider);
    final statsAsync = ref.watch(questionBankStatsProvider);
    final t = AppLocalizations.of(ref);
    const types = [null, 'mcq', 'true_false', 'short_answer', 'essay'];
    const difficulties = [null, 'easy', 'medium', 'hard'];

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('questionBank.title')),
        actions: [
          IconButton(
            onPressed: () => context.push('/question-bank/import'),
            icon: const Icon(Icons.upload_file_outlined),
            tooltip: t.t('questionBank.import'),
          ),
          IconButton(
            onPressed: () => context.push('/question-bank/generate'),
            icon: const Icon(Icons.auto_awesome_outlined),
            tooltip: t.t('questionBank.generate'),
          ),
        ],
      ),
      body: Column(
        children: [
          statsAsync.when(
            data: (stats) => Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: Row(
                children: [
                  Expanded(
                    child: AppStatCard(
                      label: 'Questions',
                      value: '${stats.total}',
                      icon: Icons.help_outline,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: AppStatCard(
                      label: 'Subjects',
                      value: '${stats.bySubject.length}',
                      icon: Icons.menu_book_outlined,
                    ),
                  ),
                ],
              ),
            ),
            loading: () => const SizedBox.shrink(),
            error: (_, __) => const SizedBox.shrink(),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    decoration: const InputDecoration(
                      labelText: 'Subject filter',
                    ),
                    onChanged: (value) {
                      ref.read(questionBankSubjectFilterProvider.notifier).state =
                          value.isEmpty ? null : value;
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String?>(
                    initialValue: ref.read(questionBankTypeFilterProvider),
                    decoration: const InputDecoration(labelText: 'Type'),
                    items: types
                        .map(
                          (value) => DropdownMenuItem<String?>(
                            value: value,
                            child: Text(value ?? 'All'),
                          ),
                        )
                        .toList(),
                    onChanged: (value) {
                      ref.read(questionBankTypeFilterProvider.notifier).state =
                          value;
                    },
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: DropdownButtonFormField<String?>(
                    initialValue: ref.read(questionBankDifficultyFilterProvider),
                    decoration: const InputDecoration(labelText: 'Difficulty'),
                    items: difficulties
                        .map(
                          (value) => DropdownMenuItem<String?>(
                            value: value,
                            child: Text(value ?? 'All'),
                          ),
                        )
                        .toList(),
                    onChanged: (value) {
                      ref
                          .read(questionBankDifficultyFilterProvider.notifier)
                          .state = value;
                    },
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: questionsAsync.when(
              data: (questions) {
                if (questions.isEmpty) {
                  return const AppEmptyState(
                    icon: Icons.quiz_outlined,
                    title: 'No questions available',
                  );
                }
                return RefreshIndicator(
                  onRefresh: () async {
                    ref.invalidate(questionBankQuestionsProvider);
                    ref.invalidate(questionBankStatsProvider);
                  },
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: questions.length,
                    itemBuilder: (context, index) {
                      final question = questions[index];
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
                                      question.text,
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleMedium
                                          ?.copyWith(
                                            fontWeight: FontWeight.w700,
                                          ),
                                    ),
                                  ),
                                  AppBadge(
                                    label: question.difficulty,
                                    variant: switch (question.difficulty) {
                                      'hard' => AppBadgeVariant.error,
                                      'easy' => AppBadgeVariant.success,
                                      _ => AppBadgeVariant.warning,
                                    },
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Wrap(
                                spacing: 8,
                                runSpacing: 8,
                                children: [
                                  AppBadge(label: question.subject),
                                  AppBadge(label: question.type),
                                  ...question.tags.map(
                                    (tag) => AppBadge(label: tag),
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
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _creating ? null : _createQuestion,
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
