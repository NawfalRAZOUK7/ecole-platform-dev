import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/features/academic/gradebook/gradebook_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

class TranscriptScreen extends ConsumerWidget {
  final String studentId;

  const TranscriptScreen({
    super.key,
    required this.studentId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(ref);
    final transcriptAsync = ref.watch(gradeTranscriptProvider(studentId));

    return Scaffold(
      appBar: AppBar(title: Text(t.t('gradebook.transcript'))),
      body: Semantics(
        container: true,
        label: t.t('gradebook.transcript'),
        child: transcriptAsync.when(
          data: (transcript) {
            return ListView(
              padding: const EdgeInsets.all(AppSpacing.base),
              children: [
                Text(
                  transcript.studentName,
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: AppSpacing.base),
                ...transcript.periods.map(
                  (period) => Card(
                    child: ExpansionTile(
                      title: Text(period.label),
                      subtitle: Text(
                        '${t.t('gradebook.average')}: ${period.weightedAverage.toStringAsFixed(1)}',
                      ),
                      children: period.subjects
                          .map(
                            (subject) => ListTile(
                              title: Text(subject.subjectName),
                              subtitle: Text(
                                '${subject.grades.length} ${t.t('gradebook.assessments')}',
                              ),
                              trailing: AppBadge(
                                label: subject.average.toStringAsFixed(1),
                                variant: subject.average >= 10
                                    ? AppBadgeVariant.success
                                    : AppBadgeVariant.error,
                              ),
                            ),
                          )
                          .toList(),
                    ),
                  ),
                ),
              ],
            );
          },
          error: (error, _) => AppErrorWidget(message: error.toString()),
          loading: () => const Center(child: CircularProgressIndicator()),
        ),
      ),
    );
  }
}
