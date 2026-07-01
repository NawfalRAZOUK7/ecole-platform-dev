import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'compliance_provider.dart';

class ComplianceReportScreen extends ConsumerWidget {
  const ComplianceReportScreen({super.key});

  Future<void> _generate(WidgetRef ref) async {
    await ref.read(complianceRepositoryProvider).generateReport({
      'academic_year_id': ref.read(complianceAcademicYearIdProvider),
    });
    ref.invalidate(complianceReportsProvider);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final reportsAsync = ref.watch(complianceReportsProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('compliance.reports')),
        actions: [
          IconButton(
            onPressed: () => _generate(ref),
            icon: const Icon(Icons.add_chart_outlined),
          ),
        ],
      ),
      body: Semantics(
        container: true,
        label: t.t('compliance.reports'),
        child: reportsAsync.when(
          data: (reports) {
            if (reports.isEmpty) {
              return AppEmptyState(
                icon: Icons.summarize_outlined,
                title: t.t('compliance.reportsEmpty'),
              );
            }
            return ListView(
              padding: const EdgeInsets.all(16),
              children: reports
                  .map(
                    (report) => Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        title: Text(report.title),
                        subtitle: Text(report.status),
                        trailing: report.downloadUrl == null
                            ? null
                            : const Icon(Icons.download_outlined),
                      ),
                    ),
                  )
                  .toList(),
            );
          },
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => AppErrorWidget(message: error.toString()),
        ),
      ),
    );
  }
}
