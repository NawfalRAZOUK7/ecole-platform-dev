import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/domain/entities/skills.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'skills_provider.dart';

class SkillsOverviewScreen extends ConsumerWidget {
  const SkillsOverviewScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final overviewAsync = ref.watch(skillsOverviewProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('skills.title')),
        actions: [
          IconButton(
            onPressed: () => context.push('/skills/evaluate'),
            icon: const Icon(Icons.fact_check_outlined),
          ),
          IconButton(
            onPressed: () => context.push('/skills/analytics'),
            icon: const Icon(Icons.analytics_outlined),
          ),
        ],
      ),
      body: overviewAsync.when(
        data: (overview) {
          if (overview.dimensions.isEmpty) {
            return AppEmptyState(
              icon: Icons.radar_outlined,
              title: t.t('skills.noData'),
            );
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (overview.dimensions.length >= 3) ...[
                SizedBox(
                  height: 320,
                  child: _SkillsRadarChart(items: overview.dimensions),
                ),
                const SizedBox(height: 16),
              ],
              AppStatCard(
                label: t.t('skills.overallScore'),
                value: overview.overallScore.toStringAsFixed(1),
                icon: Icons.workspace_premium_outlined,
              ),
              const SizedBox(height: 16),
              ...overview.dimensions.map(
                (item) => Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    title: Text(item.label),
                    trailing: Text(item.score.toStringAsFixed(1)),
                  ),
                ),
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}

class _SkillsRadarChart extends StatelessWidget {
  final List<SkillScoreItem> items;

  const _SkillsRadarChart({required this.items});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return RadarChart(
      RadarChartData(
        dataSets: [
          RadarDataSet(
            fillColor: theme.colorScheme.primary.withValues(alpha: 0.2),
            borderColor: theme.colorScheme.primary,
            dataEntries: items
                .map((item) => RadarEntry(value: item.score.clamp(0, 100)))
                .toList(),
          ),
        ],
        tickCount: 5,
        ticksTextStyle: theme.textTheme.labelSmall,
        tickBorderData: BorderSide(color: theme.colorScheme.outlineVariant),
        gridBorderData: BorderSide(color: theme.colorScheme.outlineVariant),
        titleTextStyle: theme.textTheme.labelMedium,
        getTitle: (index, angle) {
          return RadarChartTitle(
            text: items[index].label,
            angle: angle,
          );
        },
      ),
    );
  }
}
