import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/domain/entities/rewards.dart';
import 'package:ecole_platform/features/rewards/rewards_provider.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class StarCounter extends ConsumerWidget {
  final bool compact;

  const StarCounter({super.key, this.compact = false});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rewards = ref.watch(rewardsProvider).valueOrNull ?? StudentRewards.empty;
    final stars = rewards.stars;

    final counter = TweenAnimationBuilder<int>(
      tween: IntTween(begin: 0, end: stars),
      duration: const Duration(milliseconds: 450),
      builder: (context, value, child) {
        return Text(
          compact ? '$value' : '$value stars',
          style: TextStyle(
            fontSize: compact ? 14 : 18,
            fontWeight: FontWeight.w800,
            color: KidsContentColors.storyText,
          ),
        );
      },
    );

    if (compact) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          const Icon(
            Icons.star_rounded,
            color: KidsContentColors.starGold,
            size: 18,
          ),
          const SizedBox(width: 2),
          counter,
        ],
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.base,
        vertical: AppSpacing.sm,
      ),
      decoration: BoxDecoration(
        color: KidsContentColors.starGold.withAlpha(35),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: KidsContentColors.starGold.withAlpha(90)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          const Icon(
            Icons.auto_awesome_rounded,
            color: KidsContentColors.starGold,
            size: 24,
          ),
          const SizedBox(width: AppSpacing.sm),
          counter,
        ],
      ),
    );
  }
}
