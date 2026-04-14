/// Sami — the animated owl mascot that guides kids through content.
///
/// Usage:
/// ```dart
/// SamiMascot(
///   state: SamiState.happy,
///   message: 'Bravo ! Tu as terminé la lecture !',
///   onTap: () => ref.read(ttsServiceProvider.notifier).speak(message),
/// )
/// ```
///
/// Sami is rendered as a pure-Flutter CustomPainter owl so there are no
/// external asset dependencies. Swap with an Animated Lottie/Rive file
/// later without changing the public API.
library;

import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

// ---------------------------------------------------------------------------
// State enum
// ---------------------------------------------------------------------------

enum SamiState {
  idle,      // breathing animation
  happy,     // wings up, big smile
  thinking,  // head tilt, question mark
  speaking,  // beak opens + closes
  sleeping,  // eyes closed, ZZZ
}

// ---------------------------------------------------------------------------
// Widget
// ---------------------------------------------------------------------------

class SamiMascot extends StatefulWidget {
  final SamiState state;
  final String? message;
  final VoidCallback? onTap;
  final double size;

  const SamiMascot({
    super.key,
    this.state = SamiState.idle,
    this.message,
    this.onTap,
    this.size = 100,
  });

  @override
  State<SamiMascot> createState() => _SamiMascotState();
}

class _SamiMascotState extends State<SamiMascot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _bounce;
  late final Animation<double> _blink;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1800),
    )..repeat(reverse: true);

    _bounce = Tween<double>(begin: 0, end: 6).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );

    _blink = TweenSequence<double>([
      TweenSequenceItem(tween: ConstantTween(1.0), weight: 90),
      TweenSequenceItem(
          tween: Tween(begin: 1.0, end: 0.0), weight: 5),
      TweenSequenceItem(
          tween: Tween(begin: 0.0, end: 1.0), weight: 5),
    ]).animate(_ctrl);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: widget.onTap,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Mascot body
          AnimatedBuilder(
            animation: _ctrl,
            builder: (_, __) {
              return Transform.translate(
                offset: Offset(
                  0,
                  widget.state == SamiState.sleeping ? 0 : -_bounce.value,
                ),
                child: Transform.rotate(
                  angle: widget.state == SamiState.thinking
                      ? math.pi / 12
                      : 0,
                  child: CustomPaint(
                    size: Size(widget.size, widget.size),
                    painter: _SamiPainter(
                      state: widget.state,
                      blinkProgress: _blink.value,
                      animProgress: _ctrl.value,
                    ),
                  ),
                ),
              );
            },
          ),

          // Speech bubble
          if (widget.message != null) ...[
            const SizedBox(height: AppSpacing.xs),
            _SpeechBubble(message: widget.message!),
          ],
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Painter
// ---------------------------------------------------------------------------

class _SamiPainter extends CustomPainter {
  final SamiState state;
  final double blinkProgress;  // 1 = open, 0 = closed
  final double animProgress;   // 0..1 animation loop

  const _SamiPainter({
    required this.state,
    required this.blinkProgress,
    required this.animProgress,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height / 2;
    final r = size.width * 0.42;

    // Body
    final bodyPaint = Paint()..color = KidsContentColors.samiPrimary;
    canvas.drawCircle(Offset(cx, cy + r * 0.1), r, bodyPaint);

    // Belly
    final bellyPaint = Paint()..color = KidsContentColors.samiSecondary;
    canvas.drawOval(
      Rect.fromCenter(
          center: Offset(cx, cy + r * 0.25),
          width: r * 1.0,
          height: r * 0.8),
      bellyPaint,
    );

    // Wings (happy = raised, sleeping = tucked)
    final wingPaint = Paint()
      ..color = KidsContentColors.samiPrimary.withAlpha(200);
    if (state == SamiState.happy) {
      // Left wing (raised)
      final leftWing = Path()
        ..moveTo(cx - r * 0.9, cy)
        ..quadraticBezierTo(cx - r * 1.4, cy - r * 0.8, cx - r * 0.5, cy - r * 0.4)
        ..close();
      canvas.drawPath(leftWing, wingPaint);
      // Right wing (raised)
      final rightWing = Path()
        ..moveTo(cx + r * 0.9, cy)
        ..quadraticBezierTo(cx + r * 1.4, cy - r * 0.8, cx + r * 0.5, cy - r * 0.4)
        ..close();
      canvas.drawPath(rightWing, wingPaint);
    } else {
      // Resting wings
      final leftWing = Path()
        ..moveTo(cx - r * 0.8, cy + r * 0.1)
        ..quadraticBezierTo(cx - r * 1.2, cy + r * 0.5, cx - r * 0.4, cy + r * 0.6)
        ..close();
      canvas.drawPath(leftWing, wingPaint);
      final rightWing = Path()
        ..moveTo(cx + r * 0.8, cy + r * 0.1)
        ..quadraticBezierTo(cx + r * 1.2, cy + r * 0.5, cx + r * 0.4, cy + r * 0.6)
        ..close();
      canvas.drawPath(rightWing, wingPaint);
    }

    // Ears / horns
    final earPaint = Paint()..color = KidsContentColors.samiPrimary;
    canvas.drawCircle(Offset(cx - r * 0.5, cy - r * 0.85), r * 0.18, earPaint);
    canvas.drawCircle(Offset(cx + r * 0.5, cy - r * 0.85), r * 0.18, earPaint);

    // Eyes
    final eyeWhitePaint = Paint()..color = Colors.white;
    final eyePupilPaint = Paint()..color = const Color(0xFF1A1A2E);

    final eyeRadius = r * 0.22;
    final eyeY = cy - r * 0.15;

    // Left eye
    canvas.drawCircle(Offset(cx - r * 0.3, eyeY), eyeRadius, eyeWhitePaint);
    if (state == SamiState.sleeping) {
      // Closed eye line
      final sleepPaint = Paint()
        ..color = const Color(0xFF1A1A2E)
        ..strokeWidth = 2
        ..style = PaintingStyle.stroke;
      canvas.drawLine(
        Offset(cx - r * 0.3 - eyeRadius * 0.8, eyeY),
        Offset(cx - r * 0.3 + eyeRadius * 0.8, eyeY),
        sleepPaint,
      );
    } else {
      final pupilRadius = eyeRadius * blinkProgress;
      canvas.drawCircle(Offset(cx - r * 0.3, eyeY), pupilRadius, eyePupilPaint);
      // Shine
      canvas.drawCircle(
        Offset(cx - r * 0.3 + eyeRadius * 0.3, eyeY - eyeRadius * 0.3),
        eyeRadius * 0.2,
        eyeWhitePaint,
      );
    }

    // Right eye
    canvas.drawCircle(Offset(cx + r * 0.3, eyeY), eyeRadius, eyeWhitePaint);
    if (state == SamiState.sleeping) {
      final sleepPaint = Paint()
        ..color = const Color(0xFF1A1A2E)
        ..strokeWidth = 2
        ..style = PaintingStyle.stroke;
      canvas.drawLine(
        Offset(cx + r * 0.3 - eyeRadius * 0.8, eyeY),
        Offset(cx + r * 0.3 + eyeRadius * 0.8, eyeY),
        sleepPaint,
      );
    } else {
      final pupilRadius = eyeRadius * blinkProgress;
      canvas.drawCircle(Offset(cx + r * 0.3, eyeY), pupilRadius, eyePupilPaint);
      canvas.drawCircle(
        Offset(cx + r * 0.3 + eyeRadius * 0.3, eyeY - eyeRadius * 0.3),
        eyeRadius * 0.2,
        eyeWhitePaint,
      );
    }

    // Beak
    final beakPaint = Paint()..color = KidsContentColors.starGold;
    final beakOpen = state == SamiState.speaking ? animProgress * 4 : 0.0;
    final beakTop = cy + r * 0.15;
    final beakPath = Path()
      ..moveTo(cx - r * 0.12, beakTop)
      ..lineTo(cx, beakTop + r * 0.2 + beakOpen)
      ..lineTo(cx + r * 0.12, beakTop)
      ..close();
    canvas.drawPath(beakPath, beakPaint);

    // Thinking question mark
    if (state == SamiState.thinking) {
      final qPaint = Paint()
        ..color = KidsContentColors.levelBadge
        ..style = PaintingStyle.fill;
      canvas.drawCircle(Offset(cx + r * 1.1, cy - r * 0.8), r * 0.25, qPaint);
      final textStyle = TextStyle(
        fontSize: r * 0.28,
        color: Colors.white,
        fontWeight: FontWeight.bold,
      );
      final tp = TextPainter(
        text: TextSpan(text: '?', style: textStyle),
        textDirection: TextDirection.ltr,
      )..layout();
      tp.paint(
        canvas,
        Offset(cx + r * 1.1 - tp.width / 2, cy - r * 0.8 - tp.height / 2),
      );
    }

    // Sleeping ZZZ
    if (state == SamiState.sleeping) {
      final zStyle = TextStyle(
        fontSize: r * 0.22,
        color: KidsContentColors.samiSecondary,
        fontWeight: FontWeight.bold,
      );
      for (int i = 0; i < 3; i++) {
        final tp = TextPainter(
          text: TextSpan(text: 'z', style: zStyle),
          textDirection: TextDirection.ltr,
        )..layout();
        tp.paint(
          canvas,
          Offset(
            cx + r * (0.7 + i * 0.3),
            cy - r * (0.6 + i * 0.25),
          ),
        );
      }
    }
  }

  @override
  bool shouldRepaint(_SamiPainter old) =>
      old.state != state ||
      old.blinkProgress != blinkProgress ||
      old.animProgress != animProgress;
}

// ---------------------------------------------------------------------------
// Speech bubble
// ---------------------------------------------------------------------------

class _SpeechBubble extends StatelessWidget {
  final String message;
  const _SpeechBubble({required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(maxWidth: 240),
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md, vertical: AppSpacing.sm),
      decoration: BoxDecoration(
        color: KidsContentColors.samiBubble,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: KidsContentColors.samiBubbleBorder, width: 1.5),
        boxShadow: [
          BoxShadow(
            color: KidsContentColors.samiPrimary.withAlpha(30),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Text(
        message,
        style: const TextStyle(
          fontSize: 13,
          color: KidsContentColors.storyText,
        ),
        textAlign: TextAlign.center,
      ),
    );
  }
}
