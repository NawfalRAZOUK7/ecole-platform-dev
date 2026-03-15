/// Results screen — student grades with pull-to-refresh.
///
/// Reference: S-099, UI-STD-005

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'results_provider.dart';

class ResultsScreen extends ConsumerWidget {
  const ResultsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(resultsProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Résultats')),
      body: _buildBody(context, ref, state, theme),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref, ResultsState state,
      ThemeData theme) {
    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
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
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.assessment, size: 48, color: Colors.grey),
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
                            color: _scoreColor(r.score!, r.totalPoints)
                                .withAlpha(20),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(
                              color: _scoreColor(r.score!, r.totalPoints),
                            ),
                          ),
                          child: Text(
                            '${r.score!.toStringAsFixed(0)}/${r.totalPoints}',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: _scoreColor(r.score!, r.totalPoints),
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    r.courseTitle,
                    style: theme.textTheme.bodySmall,
                  ),
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
                        Text(
                          _formatDate(r.dueAt!),
                          style: theme.textTheme.bodySmall,
                        ),
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

  Color _scoreColor(double score, int total) {
    if (total == 0) return Colors.grey;
    final pct = score / total;
    if (pct >= 0.8) return Colors.green;
    if (pct >= 0.5) return Colors.orange;
    return Colors.red;
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
