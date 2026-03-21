/// Admin dashboard screen — summary cards with KPI metrics.
///
/// Reference: Phase 5B (from 4A) — Admin dashboard

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/admin.dart';

final _dashboardProvider =
    FutureProvider.autoDispose<DashboardStats>((ref) async {
  final repo = ref.read(adminRepositoryProvider);
  return repo.getDashboard();
});

const _roleLabels = {
  'ADM': 'Administrateurs',
  'DIR': 'Directeurs',
  'TCH': 'Enseignants',
  'PAR': 'Parents',
  'STD': 'Élèves',
};

class AdminDashboardScreen extends ConsumerWidget {
  const AdminDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboard = ref.watch(_dashboardProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Tableau de bord')),
      body: dashboard.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text(error.toString(), textAlign: TextAlign.center),
              const SizedBox(height: 16),
              FilledButton.tonal(
                onPressed: () => ref.invalidate(_dashboardProvider),
                child: const Text('Réessayer'),
              ),
            ],
          ),
        ),
        data: (stats) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(_dashboardProvider),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Summary cards
              _buildGrid(theme, [
                _StatCard(
                  icon: Icons.people,
                  label: 'Utilisateurs',
                  value: stats.totalUsers.toString(),
                  color: Colors.blue,
                ),
                _StatCard(
                  icon: Icons.devices,
                  label: 'Sessions actives',
                  value: stats.activeSessions.toString(),
                  color: Colors.green,
                ),
                _StatCard(
                  icon: Icons.mail_outline,
                  label: 'Invitations actives',
                  value: stats.activeInvitations.toString(),
                  color: Colors.orange,
                ),
                _StatCard(
                  icon: Icons.history,
                  label: 'Événements (24h)',
                  value: stats.auditEvents24h.toString(),
                  color: Colors.purple,
                ),
                _StatCard(
                  icon: Icons.pending_actions,
                  label: 'Justifications en attente',
                  value: stats.pendingJustifications.toString(),
                  color: Colors.red,
                ),
              ]),
              const SizedBox(height: 24),

              // Users by role breakdown
              Text('Répartition par rôle',
                  style: theme.textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: stats.usersByRole.entries.map((entry) {
                      final label = _roleLabels[entry.key] ?? entry.key;
                      final count = entry.value;
                      final total = stats.totalUsers > 0 ? stats.totalUsers : 1;
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Row(
                          children: [
                            SizedBox(
                                width: 100,
                                child: Text(label,
                                    style: theme.textTheme.bodySmall)),
                            Expanded(
                              child: LinearProgressIndicator(
                                value: count / total,
                                backgroundColor:
                                    theme.colorScheme.surfaceContainerHighest,
                              ),
                            ),
                            const SizedBox(width: 12),
                            Text('$count',
                                style: theme.textTheme.bodyMedium
                                    ?.copyWith(fontWeight: FontWeight.bold)),
                          ],
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildGrid(ThemeData theme, List<_StatCard> cards) {
    return Wrap(
      spacing: 12,
      runSpacing: 12,
      children: cards.map((card) {
        return SizedBox(
          width: 160,
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(card.icon, color: card.color, size: 28),
                  const SizedBox(height: 8),
                  Text(card.value,
                      style: theme.textTheme.headlineSmall
                          ?.copyWith(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text(card.label,
                      style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.onSurfaceVariant)),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}

class _StatCard {
  final IconData icon;
  final String label;
  final String value;
  final Color color;

  const _StatCard({
    required this.icon,
    required this.label,
    required this.value,
    required this.color,
  });
}
