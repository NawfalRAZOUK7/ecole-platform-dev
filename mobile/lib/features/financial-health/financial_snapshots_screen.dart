import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'financial_health_provider.dart';

class FinancialSnapshotsScreen extends ConsumerWidget {
  const FinancialSnapshotsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final snapshotAsync = ref.watch(financialSnapshotProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('financialHealth.snapshots'))),
      body: snapshotAsync.when(
        data: (snapshot) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: ListTile(
                title: Text(snapshot.snapshotDate),
                subtitle: Text(
                  'Revenue ${snapshot.revenue.toStringAsFixed(0)} • Expenses ${snapshot.expenses.toStringAsFixed(0)}',
                ),
                trailing: Text(snapshot.netPosition.toStringAsFixed(0)),
              ),
            ),
          ],
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}
