import 'package:flutter/material.dart';

import 'package:ecole_platform/domain/entities/rewards.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class StreakCard extends StatelessWidget {
  final StudentRewards rewards;

  const StreakCard({
    super.key,
    required this.rewards,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final streak = rewards.streakDays;
    final title =
        streak > 0 ? 'Serie de $streak jours' : 'Commence ta serie';
    final subtitle = streak > 0
        ? "Continue aujourd'hui pour la garder."
        : "Termine une activite aujourd'hui pour lancer ta premiere serie.";

    return Container(
      padding: const EdgeInsets.all(AppSpacing.base),
      decoration: BoxDecoration(
        color: KidsContentColors.streakOrange.withAlpha(20),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: KidsContentColors.streakOrange.withAlpha(80)),
      ),
      child: Row(
        children: <Widget>[
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(18),
            ),
            child: const Center(
              child: Text('🔥', style: TextStyle(fontSize: 26)),
            ),
          ),
          const SizedBox(width: AppSpacing.base),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: KidsContentColors.storyText,
                  ),
                ),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  subtitle,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
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
