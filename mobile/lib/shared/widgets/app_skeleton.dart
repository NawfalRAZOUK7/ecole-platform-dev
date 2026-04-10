import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/radii.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

enum SkeletonVariant { line, card, tableRow, circle }

class AppSkeleton extends StatefulWidget {
  final SkeletonVariant variant;
  final double? width;
  final double? height;
  final int count;

  const AppSkeleton({
    super.key,
    this.variant = SkeletonVariant.line,
    this.width,
    this.height,
    this.count = 1,
  });

  @override
  State<AppSkeleton> createState() => _AppSkeletonState();
}

class _AppSkeletonState extends State<AppSkeleton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1200),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Semantics(
      container: true,
      liveRegion: true,
      label: 'Loading content',
      child: ExcludeSemantics(
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, _) {
            final theme = Theme.of(context);
            final base = theme.colorScheme.surfaceContainerHighest;
            final highlight = theme.colorScheme.surfaceContainer;
            final color = Color.lerp(base, highlight, _controller.value)!;

            return Column(
              mainAxisSize: MainAxisSize.min,
              children: List.generate(
                widget.count,
                (index) => Padding(
                  padding: EdgeInsets.only(
                    bottom: index == widget.count - 1 ? 0 : AppSpacing.sm,
                  ),
                  child: _SkeletonShape(
                    variant: widget.variant,
                    width: widget.width,
                    height: widget.height,
                    color: color,
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _SkeletonShape extends StatelessWidget {
  final SkeletonVariant variant;
  final double? width;
  final double? height;
  final Color color;

  const _SkeletonShape({
    required this.variant,
    required this.width,
    required this.height,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final resolvedWidth = switch (variant) {
      SkeletonVariant.line => width ?? double.infinity,
      SkeletonVariant.card => width ?? double.infinity,
      SkeletonVariant.tableRow => width ?? double.infinity,
      SkeletonVariant.circle => width ?? 40,
    };
    final resolvedHeight = switch (variant) {
      SkeletonVariant.line => height ?? 14,
      SkeletonVariant.card => height ?? 88,
      SkeletonVariant.tableRow => height ?? 52,
      SkeletonVariant.circle => height ?? 40,
    };
    final radius = variant == SkeletonVariant.circle
        ? BorderRadius.circular(AppRadii.full)
        : BorderRadius.circular(AppRadii.md);

    return Container(
      width: resolvedWidth,
      height: resolvedHeight,
      decoration: BoxDecoration(
        color: color,
        borderRadius: radius,
      ),
    );
  }
}
