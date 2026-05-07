import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/radii.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

enum SkeletonVariant { line, card, tableRow, circle }

/// Enhanced skeleton loader with shimmer gradient animation.
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
    duration: const Duration(milliseconds: 1500),
  )..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final baseColor = theme.colorScheme.surfaceContainerHighest;
    final highlightColor = theme.colorScheme.surfaceContainer;

    return Semantics(
      container: true,
      liveRegion: true,
      label: 'Loading content',
      child: ExcludeSemantics(
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, _) {
            return ShaderMask(
              shaderCallback: (bounds) {
                return LinearGradient(
                  begin: Alignment.centerLeft,
                  end: Alignment.centerRight,
                  colors: [
                    baseColor,
                    highlightColor,
                    baseColor,
                  ],
                  stops: const [0.0, 0.5, 1.0],
                  transform: _ShimmerGradientTransform(
                    percent: _controller.value,
                  ),
                ).createShader(bounds);
              },
              blendMode: BlendMode.srcATop,
              child: Column(
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
                      color: baseColor,
                    ),
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

/// Gradient transform that slides the shimmer across the widget.
class _ShimmerGradientTransform extends GradientTransform {
  final double percent;

  const _ShimmerGradientTransform({required this.percent});

  @override
  Matrix4? transform(Rect bounds, {TextDirection? textDirection}) {
    final slideWidth = bounds.width * 2;
    final offset = slideWidth * percent - slideWidth * 0.5;
    return Matrix4.translationValues(offset, 0, 0);
  }
}

class _SkeletonShape extends StatelessWidget {
  final SkeletonVariant variant;
  final double? width;
  final double? height;
  final Color color;

  const _SkeletonShape({
    required this.variant,
    this.width,
    this.height,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final borderRadius = switch (variant) {
      SkeletonVariant.circle => BorderRadius.circular(999),
      SkeletonVariant.card => BorderRadius.circular(AppRadii.lg),
      SkeletonVariant.tableRow => BorderRadius.circular(AppRadii.sm),
      SkeletonVariant.line => BorderRadius.circular(AppRadii.sm),
    };

    final defaultHeight = switch (variant) {
      SkeletonVariant.line => 16.0,
      SkeletonVariant.card => 120.0,
      SkeletonVariant.tableRow => 48.0,
      SkeletonVariant.circle => 40.0,
    };

    final defaultWidth = switch (variant) {
      SkeletonVariant.line => double.infinity,
      SkeletonVariant.card => double.infinity,
      SkeletonVariant.tableRow => double.infinity,
      SkeletonVariant.circle => 40.0,
    };

    return Container(
      width: width ?? defaultWidth,
      height: height ?? defaultHeight,
      decoration: BoxDecoration(
        color: color,
        borderRadius: borderRadius,
      ),
    );
  }
}
