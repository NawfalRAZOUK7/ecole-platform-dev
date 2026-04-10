import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/widgets/widgets.dart';

import 'sync_provider.dart';

class SyncStatusScreen extends ConsumerWidget {
  const SyncStatusScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final statusAsync = ref.watch(syncStatusProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('sync.status'))),
      body: statusAsync.when(
        data: (bundle) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                SizedBox(
                  width: 160,
                  child: AppStatCard(
                    label: 'Queued',
                    value: '${bundle.indicator.pendingCount}',
                    icon: Icons.queue_outlined,
                  ),
                ),
                SizedBox(
                  width: 160,
                  child: AppStatCard(
                    label: 'Failed',
                    value: '${bundle.indicator.failedCount}',
                    icon: Icons.error_outline,
                  ),
                ),
                SizedBox(
                  width: 160,
                  child: AppStatCard(
                    label: 'Latency',
                    value: '${bundle.health.latencyMs.toStringAsFixed(0)} ms',
                    icon: Icons.speed_outlined,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Card(
              child: ListTile(
                title: Text(bundle.indicator.online ? 'Online' : 'Offline'),
                subtitle: Text(
                  '${t.t('sync.lastSync')}: ${bundle.indicator.lastSyncAt ?? 'n/a'}',
                ),
              ),
            ),
            const SizedBox(height: 12),
            ...bundle.devices.map(
              (device) => Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  title: Text(device.deviceName),
                  subtitle: Text(device.deviceType),
                  trailing: AppBadge(
                    label: device.isActive ? 'Active' : 'Inactive',
                    variant: device.isActive
                        ? AppBadgeVariant.success
                        : AppBadgeVariant.neutral,
                  ),
                ),
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
