/// Mini-games hub screen — entry point for kids games.
/// Hosts three game templates:
///   1. Memory Match  (flip pairs of cards)
///   2. Sorting       (drag items into correct categories)
///   3. Vocabulary    (tap the correct translation)
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/domain/entities/rewards.dart';
import 'package:ecole_platform/features/games/memory_match_game.dart';
import 'package:ecole_platform/features/games/sorting_game.dart';
import 'package:ecole_platform/features/games/vocabulary_game.dart';
import 'package:ecole_platform/features/rewards/rewards_provider.dart';
import 'package:ecole_platform/features/rewards/rewards_widgets.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class MiniGamesScreen extends ConsumerWidget {
  const MiniGamesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final rewards = ref.watch(rewardsProvider).valueOrNull ?? StudentRewards.empty;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Jeux éducatifs'),
        actions: const [StarCounter(compact: true), SizedBox(width: AppSpacing.sm)],
      ),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.base),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            LevelBadge(rewards: rewards, compact: true),
            const SizedBox(height: AppSpacing.lg),
            Text('Choisis un jeu', style: theme.textTheme.titleMedium),
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
                    label: 'Memory\nMatch',
                    color: KidsContentColors.gameBlue,
                    description: 'Retrouve les paires !',
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => MemoryMatchGame(
                          onComplete: (score) => ref
                              .read(rewardsProvider.notifier)
                              .awardMiniGameComplete('memory_match'),
                        ),
                      ),
                    ),
                  ),
                  _GameCard(
                    icon: Icons.sort,
                    label: 'Trier\nles objets',
                    color: KidsContentColors.gameGreen,
                    description: 'Classe dans la bonne case !',
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => SortingGame(
                          onComplete: (score) => ref
                              .read(rewardsProvider.notifier)
                              .awardMiniGameComplete('sorting_game'),
                        ),
                      ),
                    ),
                  ),
                  _GameCard(
                    icon: Icons.translate,
                    label: 'Vocabulaire',
                    color: KidsContentColors.gamePurple,
                    description: 'Apprends des nouveaux mots !',
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => VocabularyGame(
                          onComplete: (score) => ref
                              .read(rewardsProvider.notifier)
                              .awardMiniGameComplete('vocabulary_game'),
                        ),
                      ),
                    ),
                  ),
                  // Placeholder for a future game slot
                  _GameCard(
                    icon: Icons.lock_outline,
                    label: 'Bientôt\ndisponible',
                    color: Colors.grey.shade400,
                    description: 'Nouveau jeu en préparation',
                    locked: true,
                    onTap: () {},
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
  final bool locked;
  final VoidCallback onTap;

  const _GameCard({
    required this.icon,
    required this.label,
    required this.color,
    required this.description,
    required this.onTap,
    this.locked = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: locked ? null : onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Color banner
            Container(
              height: 90,
              color: locked ? Colors.grey.shade200 : color.withAlpha(40),
              child: Center(
                child: Icon(
                  icon,
                  size: 48,
                  color: locked ? Colors.grey : color,
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
                      color: locked ? Colors.grey : null,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: locked ? Colors.grey : theme.colorScheme.onSurface.withAlpha(150),
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
