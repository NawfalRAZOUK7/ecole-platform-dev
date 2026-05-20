import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class ConfettiOverlay extends StatefulWidget {
  final int starsEarned;
  final int xpEarned;
  final VoidCallback onDismiss;

  const ConfettiOverlay({
    super.key,
    required this.starsEarned,
    required this.xpEarned,
    required this.onDismiss,
  });

  @override
  State<ConfettiOverlay> createState() => _ConfettiOverlayState();
}

class _ConfettiOverlayState extends State<ConfettiOverlay>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scale;
  late final Animation<double> _fade;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 650),
    );
    _scale = CurvedAnimation(parent: _controller, curve: Curves.elasticOut);
    _fade = CurvedAnimation(parent: _controller, curve: Curves.easeIn);
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.onDismiss,
      child: Stack(
        children: <Widget>[
          FadeTransition(
            opacity: _fade,
            child: Container(color: Colors.black54),
          ),
          ...List<Widget>.generate(
            20,
            (int index) => _ConfettiParticle(
              index: index,
              animation: _fade,
            ),
          ),
          Center(
            child: ScaleTransition(
              scale: _scale,
              child: Container(
                margin: const EdgeInsets.all(AppSpacing.xl),
                padding: const EdgeInsets.all(AppSpacing.xl),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(28),
                  boxShadow: const <BoxShadow>[
                    BoxShadow(
                      blurRadius: 20,
                      color: Colors.black26,
                      offset: Offset(0, 8),
                    ),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    const Text('🎉', style: TextStyle(fontSize: 52)),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      'Bravo !',
                      style:
                          Theme.of(context).textTheme.headlineSmall?.copyWith(
                                fontWeight: FontWeight.w900,
                                color: KidsContentColors.storyText,
                              ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      '+${widget.starsEarned} stars  •  +${widget.xpEarned} XP',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700,
                            color: KidsContentColors.storyPageTurn,
                          ),
                    ),
                    const SizedBox(height: AppSpacing.base),
                    FilledButton(
                      onPressed: widget.onDismiss,
                      child: const Text('Continuer'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ConfettiParticle extends StatelessWidget {
  final int index;
  final Animation<double> animation;

  const _ConfettiParticle({
    required this.index,
    required this.animation,
  });

  @override
  Widget build(BuildContext context) {
    final colors = <Color>[
      KidsContentColors.starGold,
      KidsContentColors.storyPageTurn,
      KidsContentColors.gameBlue,
      KidsContentColors.gameGreen,
      KidsContentColors.gamePurple,
    ];
    final color = colors[index % colors.length];
    final screenSize = MediaQuery.of(context).size;
    final left = (((index * 37) % 100) / 100) * screenSize.width;
    final top = ((((index * 23) % 55) + 5) / 100) * screenSize.height;
    final size = 8.0 + ((index * 11) % 8).toDouble();

    return FadeTransition(
      opacity: animation,
      child: Positioned(
        left: left,
        top: top,
        child: Transform.rotate(
          angle: ((index * 13) % 16) * math.pi / 8,
          child: Container(
            width: size,
            height: size * 1.4,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(999),
            ),
          ),
        ),
      ),
    );
  }
}
