/// In-app animated splash screen.
///
/// Shown while Firebase init + cache prune complete. Reveals the École Platform
/// logo — the ring sweeps in, the graduation cap scales up, and the amber bead
/// settles on the ring — over the brand gradient, then calls [onComplete] once
/// the minimum display time is reached and init is done. Honors reduced motion
/// (MediaQuery.disableAnimations) by showing the logo immediately.

import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

class AppSplashScreen extends StatefulWidget {
  /// Called when the splash duration has elapsed and init is complete.
  final VoidCallback onComplete;

  /// Future representing background initialization work (Firebase + cache).
  final Future<void> initFuture;

  const AppSplashScreen({
    super.key,
    required this.onComplete,
    required this.initFuture,
  });

  @override
  State<AppSplashScreen> createState() => _AppSplashScreenState();
}

class _AppSplashScreenState extends State<AppSplashScreen>
    with TickerProviderStateMixin {
  late final AnimationController _fadeController;
  late final AnimationController _revealController;
  late final Animation<double> _fadeAnim;
  late final Animation<double> _ring;
  late final Animation<double> _cap;
  late final Animation<double> _bead;
  late final Animation<double> _word;

  bool _initDone = false;
  bool _minTimeDone = false;

  @override
  void initState() {
    super.initState();

    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 400),
    );
    _fadeAnim = CurvedAnimation(parent: _fadeController, curve: Curves.easeOut);

    _revealController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1300),
    );
    _ring = CurvedAnimation(
      parent: _revealController,
      curve: const Interval(0.0, 0.7, curve: Curves.easeOutCubic),
    );
    _cap = CurvedAnimation(
      parent: _revealController,
      curve: const Interval(0.2, 0.75, curve: Curves.easeOutBack),
    );
    _bead = CurvedAnimation(
      parent: _revealController,
      curve: const Interval(0.62, 1.0, curve: Curves.easeOut),
    );
    _word = CurvedAnimation(
      parent: _revealController,
      curve: const Interval(0.55, 1.0, curve: Curves.easeOut),
    );

    _fadeController.forward();
    _revealController.forward();

    Future.delayed(const Duration(seconds: 2), _markMinTimeDone);
    widget.initFuture
        .then((_) => _markInitDone())
        .catchError((_) => _markInitDone());
  }

  void _markMinTimeDone() {
    _minTimeDone = true;
    _maybeComplete();
  }

  void _markInitDone() {
    _initDone = true;
    _maybeComplete();
  }

  void _maybeComplete() {
    if (_initDone && _minTimeDone && mounted) {
      widget.onComplete();
    }
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _revealController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const white = Colors.white;
    final reduced = MediaQuery.of(context).disableAnimations;
    if (reduced) {
      _revealController.value = 1.0;
    }

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF2563EB), Color(0xFF5B5BEF), Color(0xFF8B5CF6)],
            stops: [0.0, 0.55, 1.0],
          ),
        ),
        child: FadeTransition(
          opacity: _fadeAnim,
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                SizedBox(
                  width: 132,
                  height: 132,
                  child: AnimatedBuilder(
                    animation: _revealController,
                    builder: (context, _) => CustomPaint(
                      painter: _LogoPainter(
                        ring: _ring.value,
                        cap: _cap.value.clamp(0.0, 1.0),
                        bead: _bead.value,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),
                FadeTransition(
                  opacity: _word,
                  child: const Text(
                    'École Platform',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w800,
                      color: white,
                      fontFamily: 'Cairo',
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                FadeTransition(
                  opacity: _word,
                  child: Text(
                    'مرحباً · Bienvenue',
                    style: TextStyle(
                      fontSize: 16,
                      color: white.withAlpha(220),
                      fontFamily: 'Cairo',
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

/// Paints the École mark (ring sweep + graduation cap + amber bead) in a
/// 100-unit design space scaled to the canvas.
class _LogoPainter extends CustomPainter {
  final double ring;
  final double cap;
  final double bead;

  _LogoPainter({required this.ring, required this.cap, required this.bead});

  @override
  void paint(Canvas canvas, Size size) {
    final f = size.width / 100.0;
    Offset p(double x, double y) => Offset(x * f, y * f);

    // Ring sweep from the top.
    final ringPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.2 * f
      ..strokeCap = StrokeCap.round
      ..color = Colors.white.withAlpha(110);
    canvas.drawArc(
      Rect.fromCircle(center: p(50, 48.4), radius: 33.2 * f),
      -math.pi / 2,
      ring * 2 * math.pi,
      false,
      ringPaint,
    );

    // Graduation cap (scales + fades).
    final capAlpha = (cap.clamp(0.0, 1.0) * 255).round();
    final capPaint = Paint()..color = Colors.white.withAlpha(capAlpha);
    canvas.save();
    final c = p(50, 44);
    canvas.translate(c.dx, c.dy);
    final s = (0.6 + 0.4 * cap).clamp(0.0, 1.0);
    canvas.scale(s, s);
    canvas.translate(-c.dx, -c.dy);

    final board = Path()
      ..moveTo(p(50, 29.3).dx, p(50, 29.3).dy)
      ..lineTo(p(78.5, 41.8).dx, p(78.5, 41.8).dy)
      ..lineTo(p(50, 54.3).dx, p(50, 54.3).dy)
      ..lineTo(p(21.5, 41.8).dx, p(21.5, 41.8).dy)
      ..close();
    canvas.drawPath(board, capPaint);

    final cup = Path()
      ..moveTo(p(43.4, 52).dx, p(43.4, 52).dy)
      ..lineTo(p(56.6, 52).dx, p(56.6, 52).dy)
      ..lineTo(p(55.5, 58.6).dx, p(55.5, 58.6).dy)
      ..lineTo(p(50, 61.7).dx, p(50, 61.7).dy)
      ..lineTo(p(44.5, 58.6).dx, p(44.5, 58.6).dy)
      ..close();
    canvas.drawPath(cup, capPaint);
    canvas.drawCircle(p(50, 41.8), 2.3 * f, capPaint);
    canvas.restore();

    // Tassel + amber bead.
    final beadAlpha = (bead.clamp(0.0, 1.0) * 255).round();
    final tasselPaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.4 * f
      ..strokeCap = StrokeCap.round
      ..color = Colors.white.withAlpha(beadAlpha);
    canvas.drawLine(p(78.5, 41.8), p(78.5, 58.6), tasselPaint);
    final beadPaint = Paint()..color = const Color(0xFFF59E0B).withAlpha(beadAlpha);
    canvas.drawCircle(p(78.5, 61.7), 2.7 * f, beadPaint);
  }

  @override
  bool shouldRepaint(_LogoPainter old) =>
      old.ring != ring || old.cap != cap || old.bead != bead;
}
