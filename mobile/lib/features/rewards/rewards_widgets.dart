/// Kid-facing reward widgets: StarCounter, XpBar, LevelBadge, StreakBadge,
/// and CongratsOverlay (confetti-style celebration).
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/features/rewards/rewards_provider.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

// ---------------------------------------------------------------------------
// StarCounter — compact star display for top bar / home
// ---------------------------------------------------------------------------

class StarCounter extends ConsumerWidget {
  final bool compact;
  const StarCounter({super.key, this.compact = false});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rewards = ref.watch(rewardsProvider);
    final stars = rewards.valueOrNull?.stars ?? 0;

    if (compact) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.star_rounded,
              color: KidsContentColors.starGold, size: 18),
          const SizedBox(width: 2),
          Text('$stars',
              style: const TextStyle(
                  fontWeight: FontWeight.bold, fontSize: 14)),
        ],
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.sm, vertical: AppSpacing.xs),
      decoration: BoxDecoration(
        color: KidsContentColors.starGold.withAlpha(25),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: KidsContentColors.starGold.withAlpha(80)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.star_rounded,
              color: KidsContentColors.starGold, size: 22),
          const SizedBox(width: AppSpacing.xs),
          Text(
            '$stars étoiles',
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              color: KidsContentColors.storyText,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// XpBar — progress towards next level
// ---------------------------------------------------------------------------

class XpBar extends ConsumerWidget {
  const XpBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rewards = ref.watch(rewardsProvider).valueOrNull ?? StudentRewards.empty;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            LevelBadge(level: rewards.level, small: true),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Niveau ${rewards.level}',
                    style: const TextStyle(
                        fontSize: 12, fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 4),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: TweenAnimationBuilder<double>(
                      tween: Tween(begin: 0, end: rewards.xpProgress),
                      duration: const Duration(milliseconds: 600),
                      builder: (_, value, __) => LinearProgressIndicator(
                        value: value,
                        backgroundColor: KidsContentColors.xpBarBackground,
                        color: KidsContentColors.xpBar,
                        minHeight: 8,
                      ),
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${rewards.xp % rewards.xpForNextLevel} / ${rewards.xpForNextLevel} XP',
                    style: const TextStyle(
                        fontSize: 10,
                        color: KidsContentColors.storyText),
                  ),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// LevelBadge
// ---------------------------------------------------------------------------

class LevelBadge extends StatelessWidget {
  final int level;
  final bool small;
  const LevelBadge({super.key, required this.level, this.small = false});

  @override
  Widget build(BuildContext context) {
    final size = small ? 32.0 : 48.0;
    final fontSize = small ? 12.0 : 18.0;
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: KidsContentColors.levelBadge,
        shape: BoxShape.circle,
        boxShadow: [
          BoxShadow(
              color: KidsContentColors.levelBadge.withAlpha(80),
              blurRadius: 6,
              offset: const Offset(0, 2)),
        ],
      ),
      child: Center(
        child: Text(
          '$level',
          style: TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: fontSize,
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// StreakBadge
// ---------------------------------------------------------------------------

class StreakBadge extends ConsumerWidget {
  const StreakBadge({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final streak = ref.watch(rewardsProvider).valueOrNull?.streakDays ?? 0;
    if (streak == 0) return const SizedBox.shrink();

    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.sm, vertical: AppSpacing.xs),
      decoration: BoxDecoration(
        color: KidsContentColors.streakOrange.withAlpha(25),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
            color: KidsContentColors.streakOrange.withAlpha(80)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text('🔥', style: TextStyle(fontSize: 16)),
          const SizedBox(width: 4),
          Text(
            '$streak jours',
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              color: KidsContentColors.streakOrange,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// CongratsOverlay — animated "you earned stars!" celebration
// ---------------------------------------------------------------------------

class CongratsOverlay extends StatefulWidget {
  final int starsEarned;
  final int xpEarned;
  final VoidCallback onDismiss;

  const CongratsOverlay({
    super.key,
    required this.starsEarned,
    required this.xpEarned,
    required this.onDismiss,
  });

  @override
  State<CongratsOverlay> createState() => _CongratsOverlayState();
}

class _CongratsOverlayState extends State<CongratsOverlay>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scaleAnim;
  late final Animation<double> _fadeAnim;
  final _rng = math.Random();

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _scaleAnim = CurvedAnimation(parent: _ctrl, curve: Curves.elasticOut);
    _fadeAnim = CurvedAnimation(parent: _ctrl, curve: Curves.easeIn);
    _ctrl.forward();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.onDismiss,
      child: Stack(
        children: [
          // Dim background
          FadeTransition(
            opacity: _fadeAnim,
            child: Container(color: Colors.black54),
          ),
          // Confetti particles
          ...List.generate(20, (i) => _ConfettiParticle(rng: _rng, index: i)),
          // Card
          Center(
            child: ScaleTransition(
              scale: _scaleAnim,
              child: Container(
                margin: const EdgeInsets.all(AppSpacing.xl),
                padding: const EdgeInsets.all(AppSpacing.xl),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(24),
                  boxShadow: const [
                    BoxShadow(blurRadius: 20, color: Colors.black26),
                  ],
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('🎉',
                        style: TextStyle(fontSize: 48)),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      'Bravo !',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    if (widget.starsEarned > 0) ...[
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(
                          widget.starsEarned,
                          (_) => const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 2),
                            child: Icon(Icons.star_rounded,
                                color: KidsContentColors.starGold, size: 32),
                          ),
                        ),
                      ),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        '+${widget.starsEarned} étoile${widget.starsEarned > 1 ? 's' : ''}',
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                          color: KidsContentColors.starGold,
                        ),
                      ),
                    ],
                    if (widget.xpEarned > 0) ...[
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        '+${widget.xpEarned} XP',
                        style: const TextStyle(
                          fontWeight: FontWeight.w600,
                          fontSize: 14,
                          color: KidsContentColors.xpBar,
                        ),
                      ),
                    ],
                    const SizedBox(height: AppSpacing.md),
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

class _ConfettiParticle extends StatefulWidget {
  final math.Random rng;
  final int index;
  const _ConfettiParticle({required this.rng, required this.index});

  @override
  State<_ConfettiParticle> createState() => _ConfettiParticleState();
}

class _ConfettiParticleState extends State<_ConfettiParticle>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final double _startX;
  late final double _endY;
  late final Color _color;
  late final double _size;

  static const _colors = [
    KidsContentColors.starGold,
    KidsContentColors.storyPageTurn,
    KidsContentColors.gameBlue,
    KidsContentColors.gameGreen,
    KidsContentColors.gamePurple,
  ];

  @override
  void initState() {
    super.initState();
    _startX = widget.rng.nextDouble();
    _endY = 0.3 + widget.rng.nextDouble() * 0.7;
    _color = _colors[widget.index % _colors.length];
    _size = 6 + widget.rng.nextDouble() * 8;
    _ctrl = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 800 + widget.rng.nextInt(600)),
    )..forward();
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final screen = MediaQuery.sizeOf(context);
    return AnimatedBuilder(
      animation: _ctrl,
      builder: (_, __) {
        final t = _ctrl.value;
        return Positioned(
          left: _startX * screen.width,
          top: -20 + t * screen.height * _endY,
          child: Opacity(
            opacity: (1 - t).clamp(0.0, 1.0),
            child: Transform.rotate(
              angle: t * math.pi * 4,
              child: Container(
                width: _size,
                height: _size,
                decoration: BoxDecoration(color: _color),
              ),
            ),
          ),
        );
      },
    );
  }
}
