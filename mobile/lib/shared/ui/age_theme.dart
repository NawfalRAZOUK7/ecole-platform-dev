/// Age- and niveau-based theming — Flutter parity with the web `useAgeTheme`.
///
/// Derives a tier from the Moroccan school level (`class_level`) when known,
/// otherwise from the student's date of birth. The tier scales typography,
/// card radii and control sizes so younger pupils get larger, simpler UI:
///   - maternelle (≤5 / PS·MS·GS)  : very large visuals
///   - primaire   (6-9 / CP·CE·CM) : colourful but structured (default)
///   - college    (10+ / collège)  : compact, more mature
library;

import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';

enum AgeTier { maternelle, primaire, college }

/// Map an age in full years to a tier (mirrors web `ageToTier`).
AgeTier ageTierFromAge(int age) {
  if (age <= 5) return AgeTier.maternelle;
  if (age <= 9) return AgeTier.primaire;
  return AgeTier.college;
}

/// Compute full years from a `YYYY-MM-DD` date-of-birth string.
int? ageFromDobString(String? dob) {
  if (dob == null || dob.isEmpty) return null;
  final parsed = DateTime.tryParse(dob);
  if (parsed == null) return null;
  final now = DateTime.now();
  var age = now.year - parsed.year;
  if (now.month < parsed.month ||
      (now.month == parsed.month && now.day < parsed.day)) {
    age--;
  }
  return age < 0 ? null : age;
}

/// Map a Moroccan `class_level` label to a tier when recognisable.
AgeTier? ageTierFromNiveau(String? niveau) {
  if (niveau == null || niveau.trim().isEmpty) return null;
  final n = niveau.toLowerCase();
  if (n.contains('maternelle') ||
      n.contains('prescol') ||
      RegExp(r'\b(ps|ms|gs)\b').hasMatch(n)) {
    return AgeTier.maternelle;
  }
  if (n.contains('primaire') ||
      RegExp(r'\b(cp|ce1|ce2|cm1|cm2)\b').hasMatch(n)) {
    return AgeTier.primaire;
  }
  if (n.contains('college') ||
      n.contains('collège') ||
      n.contains('lycee') ||
      n.contains('lycée') ||
      n.contains('terminale') ||
      RegExp(r'\b(6e|6eme|6ème|[1-3]\s?ac|tc|bac)\b').hasMatch(n)) {
    return AgeTier.college;
  }
  return null;
}

/// Resolve the tier: niveau first (most authoritative), then DOB, else primaire.
AgeTier resolveAgeTier({String? niveau, String? dob}) {
  final byNiveau = ageTierFromNiveau(niveau);
  if (byNiveau != null) return byNiveau;
  final age = ageFromDobString(dob);
  if (age != null) return ageTierFromAge(age);
  return AgeTier.primaire; // safe default (mirrors web fallback)
}

class _TierScale {
  final double fontFactor;
  final double cardRadius;
  final double minButtonHeight;
  final VisualDensity density;
  const _TierScale(
    this.fontFactor,
    this.cardRadius,
    this.minButtonHeight,
    this.density,
  );
}

const _scales = <AgeTier, _TierScale>{
  AgeTier.maternelle: _TierScale(1.18, 24, 56, VisualDensity.comfortable),
  AgeTier.primaire: _TierScale(1.06, 16, 48, VisualDensity.standard),
  AgeTier.college: _TierScale(1.0, 12, 44, VisualDensity.standard),
};

/// Return a copy of [base] scaled for the given age [tier].
ThemeData applyAgeTier(ThemeData base, AgeTier tier) {
  final s = _scales[tier]!;
  final radius = BorderRadius.circular(s.cardRadius);
  final buttonSize = Size.fromHeight(s.minButtonHeight);
  return base.copyWith(
    visualDensity: s.density,
    textTheme: base.textTheme.apply(fontSizeFactor: s.fontFactor),
    cardTheme: base.cardTheme.copyWith(
      shape: RoundedRectangleBorder(borderRadius: radius),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(minimumSize: buttonSize),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(minimumSize: buttonSize),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(minimumSize: buttonSize),
    ),
  );
}

StudentTierColors studentTierColors(AgeTier tier) {
  switch (tier) {
    case AgeTier.maternelle:
      return StudentTierColors.maternelle;
    case AgeTier.primaire:
      return StudentTierColors.primaire;
    case AgeTier.college:
      return StudentTierColors.college;
  }
}

ThemeData applyStudentTierColors(ThemeData base, AgeTier tier) {
  final tierColors = studentTierColors(tier);
  return base.copyWith(
    colorScheme: base.colorScheme.copyWith(
      primary: tierColors.accent,
      surface: tierColors.surface,
      onSurface: tierColors.text,
    ),
    scaffoldBackgroundColor: tierColors.background,
    cardTheme: base.cardTheme.copyWith(
      color: tierColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: base.cardTheme.shape is RoundedRectangleBorder
            ? (base.cardTheme.shape! as RoundedRectangleBorder).borderRadius
            : BorderRadius.circular(16),
        side: BorderSide(color: tierColors.border),
      ),
    ),
    navigationBarTheme: base.navigationBarTheme.copyWith(
      indicatorColor: tierColors.accentSoft,
    ),
    extensions: [
      ...base.extensions.values
          .where((extension) => extension is! StudentTierColors)
          .cast<ThemeExtension<dynamic>>(),
      tierColors,
    ],
  );
}

/// Apply the student/kids palette while keeping the app's existing typography.
ThemeData applyKidsTheme(ThemeData base) {
  final isDark = base.brightness == Brightness.dark;
  final kids = isDark ? KidsThemeColors.dark : KidsThemeColors.light;
  final semantic = isDark ? AppThemeColors.dark : AppThemeColors.light;
  final radius = BorderRadius.circular(16);

  return base.copyWith(
    colorScheme: base.colorScheme.copyWith(
      primary: kids.primary,
      secondary: AppColors.secondary,
      tertiary: kids.xp,
      surface: kids.surface,
      onSurface: kids.text,
      brightness: base.brightness,
    ),
    scaffoldBackgroundColor: kids.background,
    appBarTheme: base.appBarTheme.copyWith(
      backgroundColor: kids.background,
      foregroundColor: kids.text,
      surfaceTintColor: Colors.transparent,
      titleTextStyle: base.appBarTheme.titleTextStyle?.copyWith(
        color: kids.text,
      ),
    ),
    cardTheme: base.cardTheme.copyWith(
      color: kids.surface,
      shape: RoundedRectangleBorder(
        borderRadius: radius,
        side: BorderSide(color: kids.border),
      ),
    ),
    navigationBarTheme: base.navigationBarTheme.copyWith(
      backgroundColor: kids.surface,
      indicatorColor: kids.primaryLight.withValues(alpha: 0.24),
      labelTextStyle: WidgetStateProperty.resolveWith(
        (states) => base.textTheme.labelSmall?.copyWith(
          color: states.contains(WidgetState.selected)
              ? kids.primaryDark
              : kids.textSecondary,
          fontSize: 11,
          fontWeight: states.contains(WidgetState.selected)
              ? FontWeight.w700
              : FontWeight.w500,
        ),
      ),
    ),
    textTheme: base.textTheme.apply(
      bodyColor: kids.text,
      displayColor: kids.text,
    ),
    extensions: <ThemeExtension<dynamic>>[semantic, kids],
  );
}

/// Wraps [child] in a [Theme] scaled for the given age [tier].
class AgeThemedView extends StatelessWidget {
  final AgeTier tier;
  final bool useKidsColors;
  final Widget child;

  const AgeThemedView({
    super.key,
    required this.tier,
    this.useKidsColors = false,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    final baseTheme =
        useKidsColors ? applyKidsTheme(Theme.of(context)) : Theme.of(context);
    return Theme(
      data: applyStudentTierColors(applyAgeTier(baseTheme, tier), tier),
      child: child,
    );
  }
}
