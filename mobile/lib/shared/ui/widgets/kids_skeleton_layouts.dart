/// Kid-facing skeleton loading layouts.
///
/// Compositions of [AppSkeleton] that mimic the real content shapes on
/// each of the four kid-facing screens. Used instead of a generic
/// [CircularProgressIndicator] for a smoother, branded loading experience.

import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/widgets/app_skeleton.dart';

// ── Content list skeleton ────────────────────────────────────────────────────

/// Mimics 5 rows of the student content list:
/// [icon thumbnail] + [title + subtitle lines].
class ContentListSkeleton extends StatelessWidget {
  const ContentListSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.base),
      child: Column(
        children:
            List.generate(5, (index) => _ContentRowSkeleton(index: index)),
      ),
    );
  }
}

class _ContentRowSkeleton extends StatelessWidget {
  final int index;
  const _ContentRowSkeleton({required this.index});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: index == 4 ? 0 : AppSpacing.sm),
      child: const Row(
        children: [
          AppSkeleton(
            variant: SkeletonVariant.circle,
            width: 48,
            height: 48,
          ),
          SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppSkeleton(variant: SkeletonVariant.line, height: 14),
                SizedBox(height: AppSpacing.xs),
                AppSkeleton(
                  variant: SkeletonVariant.line,
                  height: 12,
                  width: 160,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ── Rewards skeleton ─────────────────────────────────────────────────────────

/// Mimics the rewards overview: hero card + level badge + streak + 2×2 stats.
class RewardsSkeleton extends StatelessWidget {
  const RewardsSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(AppSpacing.base),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Hero card
          AppSkeleton(
            variant: SkeletonVariant.card,
            height: 120,
          ),
          SizedBox(height: AppSpacing.base),

          // Level badge row
          Row(
            children: [
              AppSkeleton(
                variant: SkeletonVariant.circle,
                width: 56,
                height: 56,
              ),
              SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  children: [
                    AppSkeleton(variant: SkeletonVariant.line, height: 14),
                    SizedBox(height: AppSpacing.xs),
                    AppSkeleton(variant: SkeletonVariant.line, height: 10),
                  ],
                ),
              ),
            ],
          ),
          SizedBox(height: AppSpacing.base),

          // Streak bar
          AppSkeleton(variant: SkeletonVariant.line, height: 60),
          SizedBox(height: AppSpacing.base),

          // 2×2 stats grid
          Row(
            children: [
              Expanded(
                child: AppSkeleton(variant: SkeletonVariant.card, height: 80),
              ),
              SizedBox(width: AppSpacing.md),
              Expanded(
                child: AppSkeleton(variant: SkeletonVariant.card, height: 80),
              ),
            ],
          ),
          SizedBox(height: AppSpacing.md),
          Row(
            children: [
              Expanded(
                child: AppSkeleton(variant: SkeletonVariant.card, height: 80),
              ),
              SizedBox(width: AppSpacing.md),
              Expanded(
                child: AppSkeleton(variant: SkeletonVariant.card, height: 80),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Games grid skeleton ───────────────────────────────────────────────────────

/// Mimics the 2×2 games grid.
class GamesGridSkeleton extends StatelessWidget {
  const GamesGridSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.all(AppSpacing.base),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: AppSkeleton(variant: SkeletonVariant.card, height: 140),
              ),
              SizedBox(width: AppSpacing.md),
              Expanded(
                child: AppSkeleton(variant: SkeletonVariant.card, height: 140),
              ),
            ],
          ),
          SizedBox(height: AppSpacing.md),
          Row(
            children: [
              Expanded(
                child: AppSkeleton(variant: SkeletonVariant.card, height: 140),
              ),
              SizedBox(width: AppSpacing.md),
              Expanded(
                child: AppSkeleton(variant: SkeletonVariant.card, height: 140),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── Coloring grid skeleton ────────────────────────────────────────────────────

/// Mimics the coloring page grid (2×3 tall cards for image aspect ratio).
class ColoringGridSkeleton extends StatelessWidget {
  const ColoringGridSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(AppSpacing.base),
      child: Column(
        children: List.generate(3, (row) {
          return Padding(
            padding: EdgeInsets.only(bottom: row == 2 ? 0 : AppSpacing.md),
            child: const Row(
              children: [
                Expanded(
                  child: AppSkeleton(
                    variant: SkeletonVariant.card,
                    height: 180,
                  ),
                ),
                SizedBox(width: AppSpacing.md),
                Expanded(
                  child: AppSkeleton(
                    variant: SkeletonVariant.card,
                    height: 180,
                  ),
                ),
              ],
            ),
          );
        }),
      ),
    );
  }
}
