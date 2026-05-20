import 'package:flutter/material.dart';

import 'package:ecole_platform/domain/entities/ai/rewards.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class LevelBadge extends StatelessWidget {
  final StudentRewards rewards;
  final bool compact;

  const LevelBadge({
    super.key,
    required this.rewards,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: EdgeInsets.all(compact ? AppSpacing.md : AppSpacing.base),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(compact ? 20 : 28),
        border: Border.all(
          color: KidsContentColors.levelBadge.withAlpha(70),
        ),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: KidsContentColors.levelBadge.withAlpha(20),
            blurRadius: 18,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: Row(
        children: <Widget>[
          _LevelOrb(level: rewards.level, compact: compact),
          const SizedBox(width: AppSpacing.base),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'Niveau ${rewards.level}',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: KidsContentColors.storyText,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  '${rewards.xpIntoCurrentLevel} / ${rewards.xpRangeForCurrentLevel} XP',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                ClipRRect(
                  borderRadius: BorderRadius.circular(999),
                  child: LinearProgressIndicator(
                    value: rewards.levelProgress,
                    minHeight: compact ? 8 : 10,
                    backgroundColor: KidsContentColors.xpBarBackground,
                    color: KidsContentColors.xpBar,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  '${rewards.xpToNextLevel} XP jusqu\'au niveau ${rewards.level + 1}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: KidsContentColors.storyText.withAlpha(180),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _LevelOrb extends StatelessWidget {
  final int level;
  final bool compact;

  const _LevelOrb({required this.level, required this.compact});

  @override
  Widget build(BuildContext context) {
    final size = compact ? 48.0 : 64.0;
    final fontSize = compact ? 18.0 : 24.0;

    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: const LinearGradient(
          colors: <Color>[
            KidsContentColors.levelBadge,
            KidsContentColors.storyPageTurn,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: KidsContentColors.levelBadge.withAlpha(60),
            blurRadius: 14,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Center(
        child: Text(
          '$level',
          style: TextStyle(
            color: Colors.white,
            fontSize: fontSize,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
    );
  }
}
