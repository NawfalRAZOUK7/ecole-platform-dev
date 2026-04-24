/// Teacher-facing quiz analytics screen.
///
/// Phase I (Web/Mobile parity) — I6.
///
/// Mirrors `web/src/features/quizzes/QuizAnalyticsPage.tsx`:
/// * Stat cards (total attempts, completed, completion rate, avg %).
/// * Score distribution bar chart (min / avg / max).
/// * Per-question accuracy bar chart.
/// * Recent attempts list (student name, score, date, status pill).
/// * Pull-to-refresh.
library;

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'quiz_analytics_provider.dart';

class QuizAnalyticsScreen extends ConsumerWidget {
  final String quizId;

  const QuizAnalyticsScreen({super.key, required this.quizId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(ref);
    final analyticsAsync = ref.watch(quizAnalyticsProvider(quizId));
    final attemptsAsync = ref.watch(quizAttemptsProvider(quizId));

    return Scaffold(
      appBar: AppBar(title: Text(t.t('quizAnalytics.title'))),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(quizAnalyticsProvider(quizId));
          ref.invalidate(quizAttemptsProvider(quizId));
          await Future.wait([
            ref.read(quizAnalyticsProvider(quizId).future),
            ref.read(quizAttemptsProvider(quizId).future),
          ]);
        },
        child: analyticsAsync.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => AppErrorWidget(
            message: error.toString(),
            onRetry: () => ref.invalidate(quizAnalyticsProvider(quizId)),
          ),
          data: (analytics) => ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(
                analytics.title,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
              ),
              const SizedBox(height: 16),
              _StatsGrid(analytics: analytics, t: t),
              const SizedBox(height: 20),
              _ScoreDistribution(analytics: analytics, t: t),
              const SizedBox(height: 20),
              _QuestionBreakdown(analytics: analytics, t: t),
              const SizedBox(height: 20),
              _AttemptsSection(async: attemptsAsync, t: t),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatsGrid extends StatelessWidget {
  final QuizAnalytics analytics;
  final AppLocalizations t;

  const _StatsGrid({required this.analytics, required this.t});

  @override
  Widget build(BuildContext context) {
    final completionRate = analytics.completionRate;
    final avgPct = analytics.averagePercentage;
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: [
        SizedBox(
          width: 170,
          child: AppStatCard(
            label: t.t('quizAnalytics.totalAttempts'),
            value: '${analytics.totalAttempts}',
            icon: Icons.assignment_turned_in_outlined,
          ),
        ),
        SizedBox(
          width: 170,
          child: AppStatCard(
            label: t.t('quizAnalytics.completedAttempts'),
            value: '${analytics.completedAttempts}',
            icon: Icons.check_circle_outline,
          ),
        ),
        SizedBox(
          width: 170,
          child: AppStatCard(
            label: t.t('quizAnalytics.completionRate'),
            value: '${completionRate.toStringAsFixed(0)}%',
            icon: Icons.percent,
          ),
        ),
        SizedBox(
          width: 170,
          child: AppStatCard(
            label: t.t('quizAnalytics.averageScore'),
            value: avgPct != null ? '${avgPct.toStringAsFixed(1)}%' : '—',
            icon: Icons.trending_up,
          ),
        ),
      ],
    );
  }
}

class _ScoreDistribution extends StatelessWidget {
  final QuizAnalytics analytics;
  final AppLocalizations t;

  const _ScoreDistribution({required this.analytics, required this.t});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final values = <_DistributionBucket>[
      _DistributionBucket(
        label: t.t('quizAnalytics.distribution.minimum'),
        value: analytics.minScoreAchieved ?? 0,
      ),
      _DistributionBucket(
        label: t.t('quizAnalytics.distribution.average'),
        value: analytics.averageScore ?? 0,
      ),
      _DistributionBucket(
        label: t.t('quizAnalytics.distribution.maximum'),
        value: analytics.maxScoreAchieved ?? 0,
      ),
    ];
    final maxY = values.fold<double>(
          0,
          (acc, bucket) => bucket.value > acc ? bucket.value : acc,
        ) *
        1.2;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              t.t('quizAnalytics.scoreDistribution'),
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 4),
            Text(
              t.t('quizAnalytics.scoreDistributionHint'),
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 220,
              child: BarChart(
                BarChartData(
                  maxY: maxY > 0 ? maxY : 10,
                  barGroups: [
                    for (var i = 0; i < values.length; i += 1)
                      BarChartGroupData(
                        x: i,
                        barRods: [
                          BarChartRodData(
                            toY: values[i].value,
                            color: theme.colorScheme.primary,
                            width: 28,
                            borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(6),
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
                        reservedSize: 34,
                        getTitlesWidget: (value, meta) {
                          final idx = value.toInt();
                          if (idx < 0 || idx >= values.length) {
                            return const SizedBox.shrink();
                          }
                          return Padding(
                            padding: const EdgeInsets.only(top: 6),
                            child: Text(
                              values[idx].label,
                              style: theme.textTheme.labelSmall,
                            ),
                          );
                        },
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 34,
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

class _DistributionBucket {
  final String label;
  final double value;
  const _DistributionBucket({required this.label, required this.value});
}

class _QuestionBreakdown extends StatelessWidget {
  final QuizAnalytics analytics;
  final AppLocalizations t;

  const _QuestionBreakdown({required this.analytics, required this.t});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    if (analytics.questionStats.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                t.t('quizAnalytics.questionBreakdown'),
                style: theme.textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 12),
              AppEmptyState(
                icon: Icons.bar_chart,
                title: t.t('quizAnalytics.noQuestions'),
              ),
            ],
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              t.t('quizAnalytics.questionBreakdown'),
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            ...analytics.questionStats.asMap().entries.map((entry) {
              final index = entry.key;
              final q = entry.value;
              final accuracy = q.accuracy;
              final label = 'Q${index + 1}';
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        SizedBox(
                          width: 38,
                          child: Text(
                            label,
                            style: theme.textTheme.labelLarge
                                ?.copyWith(fontWeight: FontWeight.w700),
                          ),
                        ),
                        Expanded(
                          child: Text(
                            q.questionText,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: theme.textTheme.bodyMedium,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          accuracy != null
                              ? '${accuracy.toStringAsFixed(0)}%'
                              : '—',
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.w700,
                            color: _accuracyColor(accuracy, theme),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(3),
                      child: LinearProgressIndicator(
                        value: (accuracy ?? 0) / 100.0,
                        minHeight: 6,
                        backgroundColor: theme.colorScheme.surfaceContainerHighest,
                        valueColor: AlwaysStoppedAnimation(
                          _accuracyColor(accuracy, theme),
                        ),
                      ),
                    ),
                    Text(
                      '${q.correctResponses}/${q.totalResponses}',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              );
            }),
          ],
        ),
      ),
    );
  }

  Color _accuracyColor(double? accuracy, ThemeData theme) {
    if (accuracy == null) return theme.colorScheme.outline;
    if (accuracy >= 75) return Colors.green.shade600;
    if (accuracy >= 40) return Colors.orange.shade700;
    return theme.colorScheme.error;
  }
}

class _AttemptsSection extends StatelessWidget {
  final AsyncValue<List<QuizAttemptEntry>> async;
  final AppLocalizations t;

  const _AttemptsSection({required this.async, required this.t});

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
              t.t('quizAnalytics.recentAttempts'),
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),
            async.when(
              loading: () => const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, _) =>
                  AppErrorWidget(message: error.toString()),
              data: (attempts) {
                if (attempts.isEmpty) {
                  return AppEmptyState(
                    icon: Icons.history,
                    title: t.t('quizAnalytics.noAttempts'),
                  );
                }
                return Column(
                  children: attempts
                      .map((attempt) => _AttemptTile(attempt: attempt, t: t))
                      .toList(growable: false),
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _AttemptTile extends StatelessWidget {
  final QuizAttemptEntry attempt;
  final AppLocalizations t;

  const _AttemptTile({required this.attempt, required this.t});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final pct = attempt.percentage;
    final scoreText = attempt.score != null
        ? '${attempt.score!.toStringAsFixed(1)}/${attempt.maxScore}'
        : '—';
    final dateText = attempt.completedAt != null
        ? DateFormat.yMMMd().add_Hm().format(DateTime.parse(attempt.completedAt!))
        : attempt.startedAt != null
            ? DateFormat.yMMMd().add_Hm().format(DateTime.parse(attempt.startedAt!))
            : '—';

    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: CircleAvatar(
        backgroundColor: theme.colorScheme.primaryContainer,
        child: Text(
          _initials(attempt.studentName),
          style: TextStyle(
            color: theme.colorScheme.onPrimaryContainer,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      title: Text(
        attempt.studentName.isEmpty
            ? t.t('quizAnalytics.unknownStudent')
            : attempt.studentName,
        style: theme.textTheme.bodyLarge
            ?.copyWith(fontWeight: FontWeight.w600),
      ),
      subtitle: Text(
        dateText,
        style: theme.textTheme.bodySmall?.copyWith(
          color: theme.colorScheme.onSurfaceVariant,
        ),
      ),
      trailing: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text(
            pct != null ? '${pct.toStringAsFixed(0)}%' : scoreText,
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w700,
              color: _statusColor(attempt.status, pct, theme),
            ),
          ),
          Text(
            scoreText,
            style: theme.textTheme.labelSmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }

  String _initials(String name) {
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.isEmpty || parts.first.isEmpty) return '?';
    if (parts.length == 1) return parts.first.characters.first.toUpperCase();
    return (parts.first.characters.first + parts.last.characters.first)
        .toUpperCase();
  }

  Color _statusColor(String status, double? pct, ThemeData theme) {
    if (status != 'COMPLETED') return theme.colorScheme.outline;
    if (pct == null) return theme.colorScheme.onSurface;
    if (pct >= 75) return Colors.green.shade600;
    if (pct >= 50) return Colors.orange.shade700;
    return theme.colorScheme.error;
  }
}
