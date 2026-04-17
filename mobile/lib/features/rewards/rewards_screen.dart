import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/domain/entities/rewards.dart';
import 'package:ecole_platform/features/auth/auth_provider.dart';
import 'package:ecole_platform/features/rewards/rewards_provider.dart';
import 'package:ecole_platform/features/rewards/widgets/level_badge.dart';
import 'package:ecole_platform/features/rewards/widgets/star_counter.dart';
import 'package:ecole_platform/features/rewards/widgets/streak_card.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/app_empty_state.dart';
import 'package:ecole_platform/shared/widgets/app_error_widget.dart';
import 'package:ecole_platform/shared/ui/widgets/kids_skeleton_layouts.dart';

class RewardsScreen extends ConsumerWidget {
  const RewardsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    if (authState.user?.role != 'STD') {
      return const Scaffold(
        body: AppEmptyState(
          icon: Icons.lock_outline,
          title: 'Recompenses reservees aux eleves',
          subtitle: 'Cet ecran est uniquement disponible pour les comptes eleve.',
        ),
      );
    }

    final rewardsAsync = ref.watch(rewardsProvider);

    return Scaffold(
      backgroundColor: KidsContentColors.storyBackground,
      appBar: AppBar(
        title: const Text('Recompenses'),
        actions: const <Widget>[
          Padding(
            padding: EdgeInsets.only(right: AppSpacing.base),
            child: Center(child: StarCounter(compact: true)),
          ),
        ],
      ),
      body: rewardsAsync.when(
        loading: () => const RewardsSkeleton(),
        error: (error, _) => AppErrorWidget(
          message: '$error',
          onRetry: () => ref.read(rewardsProvider.notifier).refresh(),
        ),
        data: (rewards) => RefreshIndicator(
          onRefresh: () => ref.read(rewardsProvider.notifier).refresh(),
          child: ListView(
            padding: const EdgeInsets.all(AppSpacing.base),
            children: <Widget>[
              _RewardsHero(rewards: rewards),
              const SizedBox(height: AppSpacing.base),
              LevelBadge(rewards: rewards),
              const SizedBox(height: AppSpacing.base),
              StreakCard(rewards: rewards),
              const SizedBox(height: AppSpacing.base),
              _StatsGrid(rewards: rewards),
              const SizedBox(height: AppSpacing.base),
              _BadgesCard(rewards: rewards),
            ],
          ),
        ),
      ),
    );
  }
}

class _RewardsHero extends StatelessWidget {
  final StudentRewards rewards;

  const _RewardsHero({required this.rewards});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(AppSpacing.xl),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: <Color>[
            KidsContentColors.storyPageTurn,
            KidsContentColors.levelBadge,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(28),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            'Ton parcours de recompenses',
            style: theme.textTheme.titleLarge?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            "Les stars, l'XP et les series montent automatiquement pendant tes activites.",
            style: theme.textTheme.bodyMedium?.copyWith(
              color: Colors.white.withAlpha(220),
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          const StarCounter(),
        ],
      ),
    );
  }
}

class _StatsGrid extends StatelessWidget {
  final StudentRewards rewards;

  const _StatsGrid({required this.rewards});

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: AppSpacing.md,
      crossAxisSpacing: AppSpacing.md,
      childAspectRatio: 1.4,
      children: <Widget>[
        _StatCard(
          label: 'XP total',
          value: '${rewards.xp}',
          icon: Icons.bolt_rounded,
          color: KidsContentColors.gameGreen,
        ),
        _StatCard(
          label: 'Niveau actuel',
          value: '${rewards.level}',
          icon: Icons.workspace_premium_rounded,
          color: KidsContentColors.levelBadge,
        ),
        _StatCard(
          label: 'Prochain niveau dans',
          value: '${rewards.xpToNextLevel} XP',
          icon: Icons.trending_up_rounded,
          color: KidsContentColors.gameBlue,
        ),
        _StatCard(
          label: 'Badges gagnes',
          value: '${rewards.badges.length}',
          icon: Icons.verified_rounded,
          color: KidsContentColors.starGold,
        ),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;

  const _StatCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(AppSpacing.base),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: color.withAlpha(70)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: <Widget>[
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: color.withAlpha(24),
              borderRadius: BorderRadius.circular(14),
            ),
            child: Icon(icon, color: color),
          ),
          Text(
            value,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w900,
              color: KidsContentColors.storyText,
            ),
          ),
          Text(
            label,
            style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }
}

class _BadgesCard extends StatelessWidget {
  final StudentRewards rewards;

  const _BadgesCard({required this.rewards});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(AppSpacing.base),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            'Badges',
            style: theme.textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          if (rewards.badges.isEmpty)
            Text(
              "Pas encore de badge. Continue et ils apparaitront ici.",
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            )
          else
            Wrap(
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.sm,
              children: rewards.badges
                  .map(
                    (badge) => Chip(
                      avatar: const Icon(Icons.military_tech_rounded, size: 18),
                      label: Text(badge.replaceAll('_', ' ')),
                    ),
                  )
                  .toList(),
            ),
        ],
      ),
    );
  }
}
