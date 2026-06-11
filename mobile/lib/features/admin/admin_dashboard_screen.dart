/// Admin dashboard screen — summary cards with KPI metrics.
///
/// Reference: Phase 5B (from 4A) — Admin dashboard

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/admin/admin.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/widgets/platform_bridge_card.dart';

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
    final t = AppLocalizations.of(ref);
    final isRtl = ref.watch(localeProvider) == 'ar';

    return Scaffold(
      appBar: AppBar(title: Text(t.t('admin.dashboard'))),
      body: dashboard.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                size: 48,
                color: theme.colorScheme.error,
              ),
              const SizedBox(height: 16),
              Text(error.toString(), textAlign: TextAlign.center),
              const SizedBox(height: 16),
              FilledButton.tonal(
                onPressed: () => ref.invalidate(_dashboardProvider),
                child: Text(t.t('common.retry')),
              ),
            ],
          ),
        ),
        data: (stats) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(_dashboardProvider),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _StatsGrid(
                cards: [
                  _StatCard(
                    icon: Icons.people,
                    label: t.t('admin.dashboard.users'),
                    value: stats.totalUsers.toString(),
                    color: theme.colorScheme.primary,
                  ),
                  _StatCard(
                    icon: Icons.devices,
                    label: t.t('admin.dashboard.sessions'),
                    value: stats.activeSessions.toString(),
                    color: theme.semanticPalette.success,
                  ),
                  _StatCard(
                    icon: Icons.mail_outline,
                    label: t.t('admin.dashboard.invitations'),
                    value: stats.activeInvitations.toString(),
                    color: theme.semanticPalette.warning,
                  ),
                  _StatCard(
                    icon: Icons.history,
                    label: t.t('admin.dashboard.auditEvents'),
                    value: stats.auditEvents24h.toString(),
                    color: theme.colorScheme.secondary,
                  ),
                  _StatCard(
                    icon: Icons.pending_actions,
                    label: t.t('admin.dashboard.pendingJustifications'),
                    value: stats.pendingJustifications.toString(),
                    color: theme.colorScheme.error,
                  ),
                ],
              ),
              const SizedBox(height: 24),
              _SectionHeader(title: t.t('admin.dashboard.usersByRole')),
              const SizedBox(height: 12),
              _UsersByRoleCard(
                totalUsers: stats.totalUsers,
                usersByRole: stats.usersByRole,
              ),
              const SizedBox(height: 24),
              _SectionHeader(
                title: t.t('admin.dashboard.gamificationTitle'),
                subtitle: t.t('admin.dashboard.gamificationSubtitle'),
              ),
              const SizedBox(height: 12),
              _StatsGrid(
                cards: [
                  _StatCard(
                    icon: Icons.star_outlined,
                    label: t.t('admin.dashboard.starsAwardedWeek'),
                    value: stats.rewardsSummary.starsAwardedWeek.toString(),
                    color: theme.semanticPalette.warning,
                  ),
                  _StatCard(
                    icon: Icons.auto_awesome_outlined,
                    label: t.t('admin.dashboard.starsAwardedMonth'),
                    value: stats.rewardsSummary.starsAwardedMonth.toString(),
                    color: theme.colorScheme.secondary,
                  ),
                  _StatCard(
                    icon: Icons.school_outlined,
                    label: t.t('admin.dashboard.mostActiveClass'),
                    value: stats.rewardsSummary.mostActiveClass ?? '—',
                    color: theme.colorScheme.primary,
                  ),
                  _StatCard(
                    icon: Icons.workspace_premium_outlined,
                    label: t.t('admin.dashboard.recentRewardEvents'),
                    value: stats.rewardsSummary.recentRewardEvents.toString(),
                    color: theme.semanticPalette.success,
                  ),
                ],
              ),
              const SizedBox(height: 24),
              _SectionHeader(title: t.t('admin.title')),
              const SizedBox(height: 12),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.toggle_on_outlined),
                  title: Text(t.t('admin.featureToggles')),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/admin/features'),
                ),
              ),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.school_outlined),
                  title: Text(t.t('admin.schoolSettings')),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => context.push('/admin/school'),
                ),
              ),
              const SizedBox(height: 24),
              PlatformBridgeCard(
                targetPlatform: BridgePlatform.web,
                title: t.t('admin.bridgeTitle'),
                description: t.t('admin.bridgeDescription'),
                icon: Icons.admin_panel_settings_rounded,
                textDirection: isRtl ? TextDirection.rtl : TextDirection.ltr,
              ),
            ],
          ),
        ),
      ),
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

class _StatsGrid extends StatelessWidget {
  final List<_StatCard> cards;

  const _StatsGrid({required this.cards});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth < 360 ? 1 : 2;
        return GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: cards.length,
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: columns,
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: columns == 1 ? 3.2 : 1.18,
          ),
          itemBuilder: (context, index) => _MetricCard(card: cards[index]),
        );
      },
    );
  }
}

class _MetricCard extends StatelessWidget {
  final _StatCard card;

  const _MetricCard({required this.card});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: theme.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: card.color.withValues(alpha: 0.10),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(card.icon, color: card.color, size: 22),
            ),
            const SizedBox(height: 10),
            Text(
              card.value,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              card.label,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _UsersByRoleCard extends StatelessWidget {
  final int totalUsers;
  final Map<String, int> usersByRole;

  const _UsersByRoleCard({
    required this.totalUsers,
    required this.usersByRole,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final total = totalUsers > 0 ? totalUsers : 1;
    final entries = usersByRole.entries.toList()
      ..sort(
        (a, b) => (_roleLabels[a.key] ?? a.key)
            .compareTo(_roleLabels[b.key] ?? b.key),
      );

    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: theme.colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: entries.map((entry) {
            final label = _roleLabels[entry.key] ?? entry.key;
            final count = entry.value;
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Row(
                children: [
                  SizedBox(
                    width: 112,
                    child: Text(label, style: theme.textTheme.bodySmall),
                  ),
                  Expanded(
                    child: LinearProgressIndicator(
                      value: count / total,
                      minHeight: 8,
                      borderRadius: BorderRadius.circular(8),
                      backgroundColor:
                          theme.colorScheme.surfaceContainerHighest,
                    ),
                  ),
                  const SizedBox(width: 12),
                  SizedBox(
                    width: 32,
                    child: Text(
                      '$count',
                      textAlign: TextAlign.end,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ),
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  final String? subtitle;

  const _SectionHeader({
    required this.title,
    this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: theme.textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w700,
          ),
        ),
        if (subtitle != null) ...[
          const SizedBox(height: 4),
          Text(
            subtitle!,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ],
    );
  }
}
