/// In-app animated splash screen.
///
/// Shown while Firebase init + cache prune complete. Fades in the school name
/// with a bounce animation matching the Sami mascot style, then calls
/// [onComplete] when the minimum display time is reached and init is done.

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
  late final AnimationController _bounceController;
  late final Animation<double> _fadeAnim;
  late final Animation<double> _bounceAnim;

  bool _initDone = false;
  bool _minTimeDone = false;

  @override
  void initState() {
    super.initState();

    // Fade in: 500 ms
    _fadeController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 500),
    );
    _fadeAnim = CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeOut,
    );

    // Bounce: 800 ms, repeat 2×
    _bounceController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _bounceAnim = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _bounceController, curve: Curves.elasticOut),
    );

    _fadeController.forward();
    _bounceController.forward();

    // Minimum 2 s display time
    Future.delayed(const Duration(seconds: 2), _markMinTimeDone);

    // Wait for actual init work
    widget.initFuture.then((_) => _markInitDone()).catchError((_) => _markInitDone());
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
    _bounceController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    const primaryBlue = Color(0xFF2563EB);
    const white = Colors.white;

    return Scaffold(
      backgroundColor: primaryBlue,
      body: FadeTransition(
        opacity: _fadeAnim,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Bouncing logo circle
              ScaleTransition(
                scale: _bounceAnim,
                child: Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    color: white.withAlpha(30),
                    shape: BoxShape.circle,
                    border: Border.all(color: white.withAlpha(80), width: 2),
                  ),
                  child: const Center(
                    child: Text(
                      'É',
                      style: TextStyle(
                        fontSize: 64,
                        fontWeight: FontWeight.w900,
                        color: white,
                        fontFamily: 'Cairo',
                      ),
                    ),
                  ),
                ),
              ),

              const SizedBox(height: AppSpacing.lg),

              // School name
              const Text(
                'École Platform',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: white,
                  fontFamily: 'Cairo',
                  letterSpacing: 0.5,
                ),
              ),

              const SizedBox(height: AppSpacing.sm),

              // Bilingual greeting
              const Text(
                'مرحباً · Bienvenue',
                style: TextStyle(
                  fontSize: 16,
                  color: white,
                  fontFamily: 'Cairo',
                ),
              ),

              const SizedBox(height: AppSpacing.xxl),

              // Loading indicator
              SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    white.withAlpha(180),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
