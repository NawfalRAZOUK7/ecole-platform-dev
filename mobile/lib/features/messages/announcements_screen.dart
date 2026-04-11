/// Announcements screen — list with push notification support.
///
/// Reference: Phase 12B — Announcements mobile screen

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/domain/entities/conversation.dart';
import 'messages_provider.dart';

class AnnouncementsScreen extends ConsumerWidget {
  const AnnouncementsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(announcementsProvider);
    final t = AppLocalizations.of(ref);

    return Scaffold(
      appBar: AppBar(title: Text(t.t('announcements.title'))),
      body: _buildBody(context, ref, state, t),
    );
  }

  Widget _buildBody(BuildContext context, WidgetRef ref,
      AnnouncementsState state, AppLocalizations t) {
    final theme = Theme.of(context);

    if (state.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state.error != null && state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: theme.colorScheme.error),
            const SizedBox(height: 16),
            Text(state.error!),
            const SizedBox(height: 16),
            FilledButton.tonal(
              onPressed: () => ref.read(announcementsProvider.notifier).load(),
              child: Text(t.t('common.retry')),
            ),
          ],
        ),
      );
    }
    if (state.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.campaign_outlined,
                size: 48, color: theme.colorScheme.outline),
            const SizedBox(height: 16),
            Text(t.t('announcements.empty')),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => ref.read(announcementsProvider.notifier).refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: state.items.length,
        itemBuilder: (context, index) {
          final ann = state.items[index];
          return _AnnouncementCard(announcement: ann, t: t);
        },
      ),
    );
  }
}

class _AnnouncementCard extends StatelessWidget {
  final Announcement announcement;
  final AppLocalizations t;

  const _AnnouncementCard({required this.announcement, required this.t});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    String dateStr = '';
    final dateSource = announcement.publishedAt ?? announcement.createdAt;
    try {
      final dt = DateTime.parse(dateSource);
      dateStr = DateFormat.yMMMd('fr').add_Hm().format(dt);
    } catch (_) {}

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.campaign,
                    size: 20, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    announcement.title,
                    style: theme.textTheme.titleMedium
                        ?.copyWith(fontWeight: FontWeight.bold),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              announcement.body,
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                ...announcement.targetRoles.map((role) => Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: _roleChip(role, theme),
                    )),
                const Spacer(),
                Text(dateStr, style: theme.textTheme.bodySmall),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _roleChip(String role, ThemeData theme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: theme.colorScheme.secondaryContainer,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        role,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w600,
          color: theme.colorScheme.onSecondaryContainer,
        ),
      ),
    );
  }
}
