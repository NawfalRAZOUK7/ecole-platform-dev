import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'skills_provider.dart';

class SkillAnalyticsScreen extends ConsumerStatefulWidget {
  const SkillAnalyticsScreen({super.key});

  @override
  ConsumerState<SkillAnalyticsScreen> createState() =>
      _SkillAnalyticsScreenState();
}

class _SkillAnalyticsScreenState extends ConsumerState<SkillAnalyticsScreen> {
  String? _classId;

  @override
  Widget build(BuildContext context) {
    final classesAsync = ref.watch(skillsClassesProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('skills.analytics'))),
      body: classesAsync.when(
        data: (classes) {
          _classId ??= classes.isEmpty ? null : classes.first.id;
          if (_classId == null) {
            return AppEmptyState(
              icon: Icons.school_outlined,
              title: t.t('skills.noData'),
            );
          }
          final analyticsAsync = ref.watch(skillAnalyticsProvider(_classId!));
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              DropdownButtonFormField<String>(
                initialValue: _classId,
                decoration: InputDecoration(
                  labelText: t.t('skills.class'),
                  border: const OutlineInputBorder(),
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
                  setState(() => _classId = value);
                },
              ),
              const SizedBox(height: 16),
              analyticsAsync.when(
                data: (bundle) => Column(
                  children: [
                    AppStatCard(
                      label: t.t('skills.overallScore'),
                      value: bundle.analytics.averageScore.toStringAsFixed(1),
                      icon: Icons.workspace_premium_outlined,
                    ),
                    const SizedBox(height: 16),
                    ...bundle.analytics.dimensions.map(
                      (item) => Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          title: Text(item.label),
                          trailing: Text(item.score.toStringAsFixed(1)),
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        t.t('skills.leaderboard'),
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.w700,
                            ),
                      ),
                    ),
                    const SizedBox(height: 12),
                    ...bundle.leaderboard.map(
                      (entry) => Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          leading: const Icon(Icons.emoji_events_outlined),
                          title: Text(entry.studentName),
                          trailing: Text(entry.score.toStringAsFixed(1)),
                        ),
                      ),
                    ),
                  ],
                ),
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (error, _) => AppErrorWidget(message: error.toString()),
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
