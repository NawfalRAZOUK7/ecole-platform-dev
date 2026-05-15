/// Teacher-facing quiz list screen (read-only + publish toggle).
///
/// Phase I (Web/Mobile parity) — I7.
///
/// Mirrors `web/src/features/teacher/QuizManagerPage.tsx` but read-only for
/// mobile — create/edit flows remain on the web. Teachers can:
/// * Browse their quizzes.
/// * Filter by status (all / published / draft).
/// * Search by title.
/// * Tap a quiz to open its analytics (`/quizzes/{id}/analytics`, see I6).
/// * Long-press to toggle publish/unpublish.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'teacher_quiz_list_provider.dart';

class TeacherQuizListScreen extends ConsumerStatefulWidget {
  const TeacherQuizListScreen({super.key});

  @override
  ConsumerState<TeacherQuizListScreen> createState() =>
      _TeacherQuizListScreenState();
}

class _TeacherQuizListScreenState extends ConsumerState<TeacherQuizListScreen> {
  late final TextEditingController _searchController;

  @override
  void initState() {
    super.initState();
    _searchController = TextEditingController();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(ref);
    final async = ref.watch(teacherQuizListProvider);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('teacherQuiz.title'))),
      body: RefreshIndicator(
        onRefresh: () => ref.read(teacherQuizListProvider.notifier).refresh(),
        child: async.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => ListView(
            padding: const EdgeInsets.all(16),
            children: [
              AppErrorWidget(
                message: error.toString(),
                onRetry: () =>
                    ref.read(teacherQuizListProvider.notifier).refresh(),
              ),
            ],
          ),
          data: (state) => _Body(
            state: state,
            t: t,
            searchController: _searchController,
            onFilterChanged: (filter) =>
                ref.read(teacherQuizListProvider.notifier).setFilter(filter),
            onSearchChanged: (value) => ref
                .read(teacherQuizListProvider.notifier)
                .setSearchQuery(value),
            onTap: (quiz) => context.push('/quizzes/${quiz.id}/analytics'),
            onLongPress: (quiz) => _confirmTogglePublish(context, ref, t, quiz),
          ),
        ),
      ),
    );
  }

  Future<void> _confirmTogglePublish(
    BuildContext context,
    WidgetRef ref,
    AppLocalizations t,
    TeacherQuizSummary quiz,
  ) async {
    final publishing = !quiz.isPublished;
    final messenger = ScaffoldMessenger.of(context);
    final confirmed = await AppConfirmDialog.show(
      context,
      title: publishing
          ? t.t('teacherQuiz.confirmPublishTitle')
          : t.t('teacherQuiz.confirmUnpublishTitle'),
      message: publishing
          ? t.t('teacherQuiz.confirmPublishMessage')
          : t.t('teacherQuiz.confirmUnpublishMessage'),
      confirmLabel: publishing
          ? t.t('teacherQuiz.publish')
          : t.t('teacherQuiz.unpublish'),
      cancelLabel: t.t('teacherQuiz.cancel'),
    );
    if (!confirmed) return;
    try {
      await ref.read(teacherQuizListProvider.notifier).togglePublish(quiz);
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            publishing
                ? t.t('teacherQuiz.publishSuccess')
                : t.t('teacherQuiz.unpublishSuccess'),
          ),
        ),
      );
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(content: Text('${t.t('teacherQuiz.toggleError')}: $e')),
      );
    }
  }
}

class _Body extends StatelessWidget {
  final TeacherQuizListState state;
  final AppLocalizations t;
  final TextEditingController searchController;
  final ValueChanged<TeacherQuizFilter> onFilterChanged;
  final ValueChanged<String> onSearchChanged;
  final ValueChanged<TeacherQuizSummary> onTap;
  final ValueChanged<TeacherQuizSummary> onLongPress;

  const _Body({
    required this.state,
    required this.t,
    required this.searchController,
    required this.onFilterChanged,
    required this.onSearchChanged,
    required this.onTap,
    required this.onLongPress,
  });

  @override
  Widget build(BuildContext context) {
    final quizzes = state.visibleQuizzes;
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
      children: [
        TextField(
          controller: searchController,
          onChanged: onSearchChanged,
          decoration: InputDecoration(
            hintText: t.t('teacherQuiz.searchHint'),
            prefixIcon: const Icon(Icons.search),
            border: const OutlineInputBorder(),
            isDense: true,
          ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          children: [
            _FilterChip(
              label: t.t('teacherQuiz.filter.all'),
              selected: state.filter == TeacherQuizFilter.all,
              onSelected: () => onFilterChanged(TeacherQuizFilter.all),
            ),
            _FilterChip(
              label: t.t('teacherQuiz.filter.published'),
              selected: state.filter == TeacherQuizFilter.published,
              onSelected: () => onFilterChanged(TeacherQuizFilter.published),
            ),
            _FilterChip(
              label: t.t('teacherQuiz.filter.draft'),
              selected: state.filter == TeacherQuizFilter.draft,
              onSelected: () => onFilterChanged(TeacherQuizFilter.draft),
            ),
          ],
        ),
        const SizedBox(height: 16),
        if (quizzes.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 48),
            child: AppEmptyState(
              icon: Icons.quiz_outlined,
              title: t.t('teacherQuiz.empty'),
              subtitle: t.t('teacherQuiz.emptySubtitle'),
            ),
          )
        else
          ...quizzes.map(
            (quiz) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _QuizCard(
                quiz: quiz,
                t: t,
                onTap: () => onTap(quiz),
                onLongPress: () => onLongPress(quiz),
              ),
            ),
          ),
      ],
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onSelected;

  const _FilterChip({
    required this.label,
    required this.selected,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => onSelected(),
    );
  }
}

class _QuizCard extends StatelessWidget {
  final TeacherQuizSummary quiz;
  final AppLocalizations t;
  final VoidCallback onTap;
  final VoidCallback onLongPress;

  const _QuizCard({
    required this.quiz,
    required this.t,
    required this.onTap,
    required this.onLongPress,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        onLongPress: onLongPress,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      quiz.title,
                      style: theme.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                  ),
                  const SizedBox(width: 8),
                  _StatusPill(status: quiz.status, t: t),
                ],
              ),
              if (quiz.description != null &&
                  quiz.description!.trim().isNotEmpty) ...[
                const SizedBox(height: 6),
                Text(
                  quiz.description!,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
              const SizedBox(height: 12),
              Wrap(
                spacing: 12,
                runSpacing: 4,
                children: [
                  _MetaChip(
                    icon: Icons.help_outline,
                    label: t.t('teacherQuiz.questions').replaceAll(
                          '{n}',
                          '${quiz.questionCount}',
                        ),
                  ),
                  _MetaChip(
                    icon: Icons.star_outline,
                    label: t.t('teacherQuiz.points').replaceAll(
                          '{n}',
                          '${quiz.totalPoints}',
                        ),
                  ),
                  if (quiz.timeLimitMinutes != null)
                    _MetaChip(
                      icon: Icons.timer_outlined,
                      label: t.t('teacherQuiz.timeLimit').replaceAll(
                            '{n}',
                            '${quiz.timeLimitMinutes}',
                          ),
                    ),
                  if (quiz.subject != null && quiz.subject!.isNotEmpty)
                    _MetaChip(
                      icon: Icons.book_outlined,
                      label: quiz.subject!,
                    ),
                  if (quiz.levelBand != null && quiz.levelBand!.isNotEmpty)
                    _MetaChip(
                      icon: Icons.school_outlined,
                      label: quiz.levelBand!,
                    ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                t.t('teacherQuiz.longPressHint'),
                style: theme.textTheme.labelSmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  final String status;
  final AppLocalizations t;

  const _StatusPill({required this.status, required this.t});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final published = status.toLowerCase() == 'published';
    final color = published
        ? Colors.green.shade600
        : status.toLowerCase() == 'archived'
            ? theme.colorScheme.outline
            : theme.colorScheme.tertiary;
    final label = published
        ? t.t('teacherQuiz.status.published')
        : status.toLowerCase() == 'archived'
            ? t.t('teacherQuiz.status.archived')
            : t.t('teacherQuiz.status.draft');
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(
        label,
        style: theme.textTheme.labelSmall?.copyWith(
          color: color,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _MetaChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: theme.colorScheme.onSurfaceVariant),
        const SizedBox(width: 4),
        Text(
          label,
          style: theme.textTheme.labelSmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}
