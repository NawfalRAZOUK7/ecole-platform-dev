import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'sync_provider.dart';

class SyncConflictsScreen extends ConsumerWidget {
  const SyncConflictsScreen({super.key});

  Future<void> _resolve(WidgetRef ref, String id) async {
    await ref.read(syncRepositoryProvider).resolveConflict(id, {
      'resolution': 'resolved',
      'strategy': 'server_wins',
    });
    ref.invalidate(syncConflictsProvider);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final conflictsAsync = ref.watch(syncConflictsProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('sync.conflicts'))),
      body: conflictsAsync.when(
        data: (conflicts) {
          if (conflicts.isEmpty) {
            return AppEmptyState(
              icon: Icons.rule_folder_outlined,
              title: t.t('sync.noConflicts'),
            );
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: conflicts
                .map(
                  (conflict) => Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            conflict.summary,
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          const SizedBox(height: 8),
                          Text('${conflict.entityType} • ${conflict.entityId}'),
                          const SizedBox(height: 12),
                          Align(
                            alignment: Alignment.centerRight,
                            child: FilledButton.tonal(
                              onPressed: () => _resolve(ref, conflict.id),
                              child: Text(t.t('sync.resolve')),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                )
                .toList(),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => AppErrorWidget(message: error.toString()),
      ),
    );
  }
}
