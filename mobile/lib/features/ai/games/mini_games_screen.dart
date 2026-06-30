/// Mini-games hub screen — entry point for kids games.
/// Hosts three game templates:
///   1. Memory Match  (flip pairs of cards)
///   2. Sorting       (drag items into correct categories)
///   3. Vocabulary    (tap the correct translation)
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:ecole_platform/domain/entities/ai/rewards.dart';
import 'package:ecole_platform/l10n/app_localizations.dart';
import 'package:ecole_platform/features/ai/rewards/rewards_provider.dart';
import 'package:ecole_platform/features/ai/rewards/rewards_widgets.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/ui/widgets/kids_skeleton_layouts.dart';

class MiniGamesScreen extends ConsumerWidget {
  const MiniGamesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final t = AppLocalizations.of(ref);
    final rewardsAsync = ref.watch(rewardsProvider);
    if (rewardsAsync.isLoading) {
      return Scaffold(
        appBar: AppBar(title: Text(t.t('games.title'))),
        body: const GamesGridSkeleton(),
      );
    }
    final rewards = rewardsAsync.valueOrNull ?? StudentRewards.empty;

    return Scaffold(
      appBar: AppBar(
        title: Text(t.t('games.title')),
        actions: const [
          StarCounter(compact: true),
          SizedBox(width: AppSpacing.sm),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.base),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            LevelBadge(rewards: rewards, compact: true),
            const SizedBox(height: AppSpacing.lg),
            Text(t.t('games.chooseGame'), style: theme.textTheme.titleMedium),
            const SizedBox(height: AppSpacing.md),
            Expanded(
              child: GridView.count(
                crossAxisCount: 2,
                mainAxisSpacing: AppSpacing.md,
                crossAxisSpacing: AppSpacing.md,
                childAspectRatio: 0.85,
                children: [
                  _GameCard(
                    icon: Icons.grid_on,
                    label: t.t('games.memoryLabel'),
                    color: KidsContentColors.gameBlue,
                    description: t.t('games.memoryDesc'),
                    onTap: () => context.push('/games/memory'),
                  ),
                  _GameCard(
                    icon: Icons.sort,
                    label: t.t('games.sortingLabel'),
                    color: KidsContentColors.gameGreen,
                    description: t.t('games.sortingDesc'),
                    onTap: () => context.push('/games/sorting'),
                  ),
                  _GameCard(
                    icon: Icons.translate,
                    label: t.t('games.vocabLabel'),
                    color: KidsContentColors.gamePurple,
                    description: t.t('games.vocabDesc'),
                    onTap: () => context.push('/games/vocabulary'),
                  ),
                  _GameCard(
                    icon: Icons.extension,
                    label: t.t('games.puzzleLabel'),
                    color: KidsContentColors.gameYellow,
                    description: t.t('games.puzzleDesc'),
                    onTap: () => context.push('/games/letter-puzzle'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GameCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final String description;
  final VoidCallback onTap;

  const _GameCard({
    required this.icon,
    required this.label,
    required this.color,
    required this.description,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Color banner
            Container(
              height: 90,
              color: color.withAlpha(40),
              child: Center(
                child: Icon(
                  icon,
                  size: 48,
                  color: color,
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(AppSpacing.sm),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.onSurface.withAlpha(150),
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
