/// Shared motion language for the app.
///
/// A single page-transition vocabulary (fade + subtle slide-up on an
/// easeOutCubic curve) applied to every route via [appPageTransitionsTheme],
/// plus the canonical durations/curves used by the reusable motion widgets.
///
/// Reduced motion: [AppPageTransitionsBuilder] returns the child unanimated when
/// the platform requests reduced animations (`MediaQuery.disableAnimations`).
/// The vertical slide keeps transitions RTL-safe.

import 'package:flutter/material.dart';

/// Canonical motion timings — keep all animations on these values.
class AppMotion {
  AppMotion._();

  static const Duration micro = Duration(milliseconds: 150);
  static const Duration standard = Duration(milliseconds: 250);
  static const Duration page = Duration(milliseconds: 350);

  static const Curve curve = Curves.easeOutCubic;
  static const Curve reverseCurve = Curves.easeInCubic;
}

/// Fade + small slide-up page transition, used for all platforms.
class AppPageTransitionsBuilder extends PageTransitionsBuilder {
  const AppPageTransitionsBuilder();

  @override
  Widget buildTransitions<T>(
    PageRoute<T> route,
    BuildContext context,
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  ) {
    if (MediaQuery.of(context).disableAnimations) return child;

    final curved = CurvedAnimation(
      parent: animation,
      curve: AppMotion.curve,
      reverseCurve: AppMotion.reverseCurve,
    );

    return FadeTransition(
      opacity: curved,
      child: SlideTransition(
        position: Tween<Offset>(
          begin: const Offset(0, 0.02),
          end: Offset.zero,
        ).animate(curved),
        child: child,
      ),
    );
  }
}

/// Drop-in [PageTransitionsTheme] for [ThemeData.pageTransitionsTheme].
const PageTransitionsTheme appPageTransitionsTheme = PageTransitionsTheme(
  builders: <TargetPlatform, PageTransitionsBuilder>{
    TargetPlatform.android: AppPageTransitionsBuilder(),
    TargetPlatform.iOS: AppPageTransitionsBuilder(),
    TargetPlatform.macOS: AppPageTransitionsBuilder(),
    TargetPlatform.windows: AppPageTransitionsBuilder(),
    TargetPlatform.linux: AppPageTransitionsBuilder(),
    TargetPlatform.fuchsia: AppPageTransitionsBuilder(),
  },
);
