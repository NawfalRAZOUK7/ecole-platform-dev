/// Results screen — student/parent grades with pull-to-refresh.
///
/// Reference: S-099, UI-STD-005
/// Phase 10C: Added quiz results tab for parent dashboard.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/quiz.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'results_provider.dart';

class ResultsScreen extends ConsumerStatefulWidget {
  const ResultsScreen({super.key});

  @override
  ConsumerState<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends ConsumerState<ResultsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<QuizResultSummary> _quizResults = [];
  bool _quizLoading = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _fetchQuizResults();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetchQuizResults() async {
    setState(() {
      _quizLoading = true;
    });
    try {
      final repo = ref.read(quizRepositoryProvider);
      _quizResults = await repo.getQuizResults();
      setState(() => _quizLoading = false);
    } catch (e) {
      setState(() {
        _quizLoading = false;
        // Silently ignore if endpoint not available
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(resultsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Résultats'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Devoirs'),
            Tab(text: 'Quiz'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildAssignmentsTab(context, ref, state, theme),
          _buildQuizTab(context, theme),
        ],
      ),
    );
  }

  // ── Assignments Tab (original) ──

  Widget _buildAssignmentsTab(BuildContext context, WidgetRef ref,
      ResultsState state, ThemeData theme) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
            const SizedBox(height: 16),
            Text(state.error!, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(resultsProvider.notifier).load(),
              child: const Text('Réessayer'),
            ),
          ],
        ),
      );
    }

    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.assessment, size: 48, color: theme.colorScheme.outline),
            SizedBox(height: 16),
            Text('Aucun résultat disponible'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(resultsProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length,
        itemBuilder: (context, index) {
          final r = state.items[index];
          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          r.assignmentTitle,
                          style: theme.textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w600),
                        ),
                      ),
                      if (r.score != null)
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 4),
                          decoration: BoxDecoration(
                            color: _scoreColor(theme, r.score!, r.totalPoints)
                                .withAlpha(20),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color:
                                  _scoreColor(theme, r.score!, r.totalPoints),
                            ),
                          ),
                          child: Text(
                            '${r.score!.toStringAsFixed(0)}/${r.totalPoints}',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color:
                                  _scoreColor(theme, r.score!, r.totalPoints),
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(r.courseTitle, style: theme.textTheme.bodySmall),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      if (r.status != null)
                        Chip(
                          label: Text(r.status!,
                              style: const TextStyle(fontSize: 11)),
                          padding: EdgeInsets.zero,
                          visualDensity: VisualDensity.compact,
                          materialTapTargetSize:
                              MaterialTapTargetSize.shrinkWrap,
                        ),
                      const Spacer(),
                      if (r.dueAt != null)
                        Text(_formatDate(r.dueAt!),
                            style: theme.textTheme.bodySmall),
                    ],
                  ),
                  if (r.feedbackText != null) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(r.feedbackText!,
                          style: theme.textTheme.bodySmall),
                    ),
                  ],
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  // ── Quiz Results Tab (Phase 10C) ──

  Widget _buildQuizTab(BuildContext context, ThemeData theme) {
    if (_quizLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_quizResults.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.quiz, size: 48, color: theme.colorScheme.outline),
            const SizedBox(height: 16),
            const Text('Aucun résultat de quiz'),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchQuizResults,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _quizResults.length,
        itemBuilder: (context, index) {
          final q = _quizResults[index];
          final score = q.score ?? 0;
          final maxScore = q.maxScore ?? 1;
          final pct = maxScore > 0 ? score / maxScore : 0.0;

          return Card(
            margin: const EdgeInsets.only(bottom: 12),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          q.quizTitle,
                          style: theme.textTheme.titleMedium
                              ?.copyWith(fontWeight: FontWeight.w600),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 4),
                        decoration: BoxDecoration(
                          color: _pctColor(theme, pct).withAlpha(20),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: _pctColor(theme, pct)),
                        ),
                        child: Text(
                          '${score.toStringAsFixed(0)}/${maxScore.toStringAsFixed(0)}',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: _pctColor(theme, pct),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Chip(
                        label: Text('Tentative ${q.attemptNo}',
                            style: const TextStyle(fontSize: 11)),
                        padding: EdgeInsets.zero,
                        visualDensity: VisualDensity.compact,
                        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '${(pct * 100).toStringAsFixed(0)}%',
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          color: _pctColor(theme, pct),
                        ),
                      ),
                      const Spacer(),
                      if (q.completedAt != null)
                        Text(
                          _formatDate(q.completedAt!),
                          style: theme.textTheme.bodySmall,
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
  }

  Color _scoreColor(ThemeData theme, double score, int total) {
    if (total == 0) return theme.colorScheme.outline;
    final pct = score / total;
    if (pct >= 0.8) return theme.semanticPalette.success;
    if (pct >= 0.5) return theme.semanticPalette.warning;
    return theme.colorScheme.error;
  }

  Color _pctColor(ThemeData theme, double pct) {
    if (pct >= 0.8) return theme.semanticPalette.success;
    if (pct >= 0.5) return theme.semanticPalette.warning;
    return theme.colorScheme.error;
  }

  String _formatDate(String dateStr) {
    try {
      final date = DateTime.parse(dateStr);
      return DateFormat.yMMMd('fr').format(date);
    } catch (_) {
      return dateStr;
    }
  }
}
