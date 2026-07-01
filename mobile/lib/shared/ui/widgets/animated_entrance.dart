/// Reusable entrance animation for content and list items.
///
/// Fades and slides its child in on first build using the shared motion
/// vocabulary ([AppMotion]). Use [AnimatedEntrance.stagger] to compute a capped
/// per-index delay for list/grid reveals (the cap avoids absurd delays deep in
/// long lists). Returns the child unanimated when the platform requests reduced
/// animations. The vertical-only offset keeps it RTL-safe.

import 'package:flutter/material.dart';
import 'package:ecole_platform/shared/ui/motion.dart';

class AnimatedEntrance extends StatefulWidget {
  final Widget child;
  final Duration delay;
  final Duration duration;
  final double offsetY;

  const AnimatedEntrance({
    super.key,
    required this.child,
    this.delay = Duration.zero,
    this.duration = AppMotion.standard,
    this.offsetY = 12,
  });

  /// Capped stagger delay for list items (index 0,1,2… → 0,step,2·step…),
  /// clamped at [max] steps so deep items don't wait forever.
  static Duration stagger(
    int index, {
    Duration step = const Duration(milliseconds: 45),
    int max = 8,
  }) {
    final i = index < 0 ? 0 : (index > max ? max : index);
    return step * i;
  }

  @override
  State<AnimatedEntrance> createState() => _AnimatedEntranceState();
}

class _AnimatedEntranceState extends State<AnimatedEntrance>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: widget.duration,
  );
  late final Animation<double> _anim = CurvedAnimation(
    parent: _controller,
    curve: AppMotion.curve,
  );
  bool _started = false;

  void _startOnce() {
    if (_started) return;
    _started = true;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (widget.delay == Duration.zero) {
        _controller.forward();
      } else {
        Future.delayed(widget.delay, () {
          if (mounted) _controller.forward();
        });
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (MediaQuery.of(context).disableAnimations) return widget.child;
    _startOnce();
    return FadeTransition(
      opacity: _anim,
      child: AnimatedBuilder(
        animation: _anim,
        builder: (context, child) => Transform.translate(
          offset: Offset(0, (1 - _anim.value) * widget.offsetY),
          child: child,
        ),
        child: widget.child,
      ),
    );
  }
}
