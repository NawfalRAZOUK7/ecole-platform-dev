/// Shimmer skeleton placeholders for list loads.
///
/// Drop-in replacement for a full-screen `CircularProgressIndicator` on list
/// screens: keeps the page's shape while data arrives, which reads as faster and
/// more polished. A single animation controller sweeps a gradient highlight
/// across all rows via [ShaderMask]. Respects reduced motion (renders static
/// placeholders when `MediaQuery.disableAnimations` is set). No dependencies.

import 'package:flutter/material.dart';

/// Animated gradient transform that slides the shimmer highlight horizontally.
class _SlideGradient extends GradientTransform {
  final double slide;
  const _SlideGradient(this.slide);

  @override
  Matrix4? transform(Rect bounds, {TextDirection? textDirection}) {
    return Matrix4.translationValues(bounds.width * (slide * 2 - 1), 0, 0);
  }
}

class MobileListSkeleton extends StatefulWidget {
  /// Number of placeholder rows.
  final int count;

  const MobileListSkeleton({super.key, this.count = 6});

  @override
  State<MobileListSkeleton> createState() => _MobileListSkeletonState();
}

class _MobileListSkeletonState extends State<MobileListSkeleton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1400),
  );

  @override
  void initState() {
    super.initState();
    _controller.repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Widget _box(
    Color color, {
    double? width,
    required double height,
    double radius = 8,
  }) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(radius),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final surface = theme.colorScheme.surface;
    final onSurface = theme.colorScheme.onSurface;
    final base = Color.alphaBlend(onSurface.withAlpha(20), surface);
    final highlight = Color.alphaBlend(onSurface.withAlpha(8), surface);

    final rows = ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: widget.count,
      itemBuilder: (context, index) => Padding(
        padding: const EdgeInsets.only(bottom: 16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            _box(base, width: 48, height: 48, radius: 24),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _box(base, width: double.infinity, height: 14),
                  const SizedBox(height: 8),
                  _box(base, width: 160, height: 12),
                ],
              ),
            ),
            const SizedBox(width: 12),
            _box(base, width: 56, height: 24, radius: 12),
          ],
        ),
      ),
    );

    if (MediaQuery.of(context).disableAnimations) return rows;

    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return ShaderMask(
          blendMode: BlendMode.srcATop,
          shaderCallback: (bounds) {
            return LinearGradient(
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
              colors: [base, highlight, base],
              stops: const [0.35, 0.5, 0.65],
              transform: _SlideGradient(_controller.value),
            ).createShader(bounds);
          },
          child: child,
        );
      },
      child: rows,
    );
  }
}
