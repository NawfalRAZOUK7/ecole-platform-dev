import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/domain/entities/rewards.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/rewards/leaderboard_provider.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/app_empty_state.dart';
import 'package:ecole_platform/shared/widgets/app_error_widget.dart';

class LeaderboardScreen extends ConsumerWidget {
  const LeaderboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(ref);
    final currentUserId = ref.watch(authProvider).user?.id;
    final leaderboardAsync = ref.watch(leaderboardProvider);

    return Scaffold(
      backgroundColor: KidsContentColors.storyBackground,
      appBar: AppBar(title: Text(t.t('leaderboard.title'))),
      body: leaderboardAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => AppErrorWidget(
          message: '$err',
          onRetry: () => ref.read(leaderboardProvider.notifier).refresh(),
        ),
        data: (data) {
          if (data.classes.isEmpty) {
            return AppEmptyState(
              icon: Icons.emoji_events_outlined,
              title: t.t('leaderboard.noClass'),
              subtitle: t.t('leaderboard.noClassSubtitle'),
            );
          }
          return RefreshIndicator(
            onRefresh: () => ref.read(leaderboardProvider.notifier).refresh(),
            child: ListView(
              padding: const EdgeInsets.all(AppSpacing.base),
              children: <Widget>[
                if (data.classes.length > 1) ...[
                  _ClassPicker(
                    classes: data.classes,
                    selectedClassId: data.selectedClassId,
                    onChanged: (classId) => ref
                        .read(leaderboardProvider.notifier)
                        .selectClass(classId),
                  ),
                  const SizedBox(height: AppSpacing.base),
                ],
                if (data.entries.isEmpty)
                  AppEmptyState(
                    icon: Icons.emoji_events_outlined,
                    title: t.t('leaderboard.empty'),
                  )
                else ...[
                  _Podium(
                    entries: data.entries,
                    currentUserId: currentUserId,
                  ),
                  const SizedBox(height: AppSpacing.base),
                  _FullList(
                    entries: data.entries,
                    currentUserId: currentUserId,
                    youLabel: t.t('leaderboard.you'),
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}

class _ClassPicker extends StatelessWidget {
  final List<StudentClassOption> classes;
  final String selectedClassId;
  final ValueChanged<String> onChanged;

  const _ClassPicker({
    required this.classes,
    required this.selectedClassId,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.base, vertical: AppSpacing.sm),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: DropdownButton<String>(
        value: selectedClassId,
        isExpanded: true,
        underline: const SizedBox.shrink(),
        items: classes
            .map((c) => DropdownMenuItem(
                  value: c.classId,
                  child: Text(c.className),
                ),)
            .toList(),
        onChanged: (v) {
          if (v != null) onChanged(v);
        },
      ),
    );
  }
}

class _Podium extends StatelessWidget {
  final List<RewardsLeaderboardEntry> entries;
  final String? currentUserId;

  const _Podium({required this.entries, required this.currentUserId});

  @override
  Widget build(BuildContext context) {
    RewardsLeaderboardEntry? findRank(int r) {
      for (final e in entries) {
        if (e.rank == r) return e;
      }
      return null;
    }

    final first = findRank(1);
    final second = findRank(2);
    final third = findRank(3);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: <Widget>[
        Expanded(
            child: _PodiumSlot(
                entry: second,
                height: 120,
                medal: '🥈',
                color: KidsContentColors.starSilver,
                currentUserId: currentUserId)),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
            child: _PodiumSlot(
                entry: first,
                height: 160,
                medal: '🥇',
                color: KidsContentColors.starGold,
                currentUserId: currentUserId)),
        const SizedBox(width: AppSpacing.sm),
        Expanded(
            child: _PodiumSlot(
                entry: third,
                height: 100,
                medal: '🥉',
                color: KidsContentColors.starBronze,
                currentUserId: currentUserId)),
      ],
    );
  }
}

class _PodiumSlot extends StatelessWidget {
  final RewardsLeaderboardEntry? entry;
  final double height;
  final String medal;
  final Color color;
  final String? currentUserId;

  const _PodiumSlot({
    required this.entry,
    required this.height,
    required this.medal,
    required this.color,
    required this.currentUserId,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isMe = entry != null && entry!.studentId == currentUserId;

    return Container(
      height: height,
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isMe ? KidsContentColors.levelBadge : color.withAlpha(120),
          width: isMe ? 3 : 2,
        ),
      ),
      child: entry == null
          ? const SizedBox.shrink()
          : Column(
              mainAxisAlignment: MainAxisAlignment.end,
              children: <Widget>[
                Text(medal, style: const TextStyle(fontSize: 28)),
                const SizedBox(height: 4),
                Text(
                  entry!.studentName,
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: theme.textTheme.bodyMedium
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 2),
                Text(
                  '⭐ ${entry!.stars} • Lv ${entry!.level}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
    );
  }
}

class _FullList extends StatelessWidget {
  final List<RewardsLeaderboardEntry> entries;
  final String? currentUserId;
  final String youLabel;

  const _FullList({
    required this.entries,
    required this.currentUserId,
    required this.youLabel,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: <Widget>[
          for (var i = 0; i < entries.length; i++)
            _LeaderRow(
              entry: entries[i],
              isMe: entries[i].studentId == currentUserId,
              showDivider: i < entries.length - 1,
              youLabel: youLabel,
              textTheme: theme.textTheme,
            ),
        ],
      ),
    );
  }
}

class _LeaderRow extends StatelessWidget {
  final RewardsLeaderboardEntry entry;
  final bool isMe;
  final bool showDivider;
  final String youLabel;
  final TextTheme textTheme;

  const _LeaderRow({
    required this.entry,
    required this.isMe,
    required this.showDivider,
    required this.youLabel,
    required this.textTheme,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: <Widget>[
        Container(
          padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.base, vertical: AppSpacing.md),
          color: isMe
              ? KidsContentColors.levelBadge.withAlpha(24)
              : Colors.transparent,
          child: Row(
            children: <Widget>[
              SizedBox(
                width: 40,
                child: Text(
                  '#${entry.rank}',
                  style: textTheme.titleMedium
                      ?.copyWith(fontWeight: FontWeight.w800),
                ),
              ),
              Expanded(
                child: Row(
                  children: <Widget>[
                    Flexible(
                      child: Text(
                        entry.studentName,
                        style: textTheme.bodyLarge?.copyWith(
                          fontWeight: isMe ? FontWeight.w800 : FontWeight.w500,
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (isMe) ...[
                      const SizedBox(width: AppSpacing.sm),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: KidsContentColors.levelBadge,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          youLabel,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              Text('⭐ ${entry.stars}',
                  style: textTheme.bodyMedium
                      ?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(width: AppSpacing.base),
              Text('Lv ${entry.level}',
                  style: textTheme.bodyMedium
                      ?.copyWith(fontWeight: FontWeight.w600)),
            ],
          ),
        ),
        if (showDivider)
          const Divider(height: 1, indent: AppSpacing.base, endIndent: AppSpacing.base),
      ],
    );
  }
}
