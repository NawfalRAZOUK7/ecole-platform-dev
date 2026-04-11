/// Parent Progress Screen — child progress summary cards with drill-down.
///
/// Reference: Phase 12C — Parent mobile progress
/// Calls GET /progress/children, taps navigate to full progress for child.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'progress_provider.dart';

/// Parent progress overview screen showing a summary card per child.
///
/// Tapping a child card navigates to [ProgressScreen] with that child's ID.
/// Data is fetched via [childrenProgressProvider] (`GET /progress/children`).
///
/// Role: PAR only.
class ParentProgressScreen extends ConsumerWidget {
  const ParentProgressScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(childrenProgressProvider);
    final t = AppLocalizations.of(ref);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('progress.parentTitle'))),
      body: _buildBody(context, ref, state, t, theme),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref,
      ChildrenProgressState state, AppLocalizations t, ThemeData theme) {
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
                  ref.read(childrenProgressProvider.notifier).load(),
              child: Text(t.t('common.retry')),
            ),
          ],
        ),
      );
    }
    if (state.children.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.school_outlined, size: 48, color: Colors.grey),
            const SizedBox(height: 16),
            Text(t.t('progress.noChildren')),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: state.children.length,
      itemBuilder: (context, index) {
        final child = state.children[index];
        return _ChildProgressCard(
          child: child,
          t: t,
          theme: theme,
          onTap: () => context.push('/progress/${child.studentId}'),
        );
      },
    );
  }
}

class _ChildProgressCard extends StatelessWidget {
  final ChildProgressSummary child;
  final AppLocalizations t;
  final ThemeData theme;
  final VoidCallback onTap;

  const _ChildProgressCard({
    required this.child,
    required this.t,
    required this.theme,
    required this.onTap,
  });

  Color _gradeColor(double v) => v >= 80
      ? Colors.green
      : v >= 50
          ? Colors.orange
          : Colors.red;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    backgroundColor: theme.colorScheme.primaryContainer,
                    child: Text(
                      child.studentName.isNotEmpty
                          ? child.studentName[0].toUpperCase()
                          : '?',
                      style: TextStyle(
                        color: theme.colorScheme.onPrimaryContainer,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      child.studentName,
                      style: theme.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w600),
                    ),
                  ),
                  const Icon(Icons.chevron_right),
                ],
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  _MetricChip(
                    label: t.t('progress.gradeAvg'),
                    value: child.gradeAverage.toStringAsFixed(1),
                    color: _gradeColor(child.gradeAverage),
                  ),
                  const SizedBox(width: 8),
                  _MetricChip(
                    label: t.t('progress.attendanceRate'),
                    value: '${child.attendanceRate.toStringAsFixed(0)}%',
                    color: child.attendanceRate >= 85
                        ? Colors.green
                        : Colors.orange,
                  ),
                  const SizedBox(width: 8),
                  _MetricChip(
                    label: t.t('progress.contentRate'),
                    value: '${child.contentCompletionRate.toStringAsFixed(0)}%',
                    color: Colors.blue,
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MetricChip extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _MetricChip(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
        decoration: BoxDecoration(
          color: color.withAlpha(20),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Column(
          children: [
            Text(value,
                style: TextStyle(
                    fontSize: 18, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 2),
            Text(label,
                style: const TextStyle(fontSize: 10, color: Colors.grey),
                textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
