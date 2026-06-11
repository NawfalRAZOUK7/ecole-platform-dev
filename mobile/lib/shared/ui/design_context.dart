import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';

enum SchoolDesignMode { formal, informal }

SchoolDesignMode resolveSchoolDesignMode({
  String? role,
  String? route,
  String? schoolType,
  String? designMode,
  Map<String, dynamic>? schoolSettings,
}) {
  final normalizedRole = (role ?? '').toUpperCase();
  if (normalizedRole == 'EDUCATOR' ||
      (route?.startsWith('/micro-schools') ?? false) ||
      (route?.startsWith('/micro/') ?? false)) {
    return SchoolDesignMode.informal;
  }

  final explicit = _normalizeMode(designMode ?? schoolSettings?['design_mode']);
  if (explicit != null) return explicit;

  return _normalizeMode(schoolType) ?? SchoolDesignMode.formal;
}

ThemeData applyInformalSchoolTheme(ThemeData base) {
  const palette = SchoolModeColors.informal;
  final radius = BorderRadius.circular(12);

  return base.copyWith(
    colorScheme: base.colorScheme.copyWith(
      primary: palette.accent,
      secondary: AppColors.success,
      surface: palette.surface,
      onSurface: palette.text,
    ),
    scaffoldBackgroundColor: palette.background,
    appBarTheme: base.appBarTheme.copyWith(
      backgroundColor: palette.background,
      foregroundColor: palette.text,
      surfaceTintColor: Colors.transparent,
    ),
    cardTheme: base.cardTheme.copyWith(
      color: palette.surface,
      shape: RoundedRectangleBorder(
        borderRadius: radius,
        side: BorderSide(color: palette.border),
      ),
    ),
    navigationBarTheme: base.navigationBarTheme.copyWith(
      backgroundColor: palette.surface,
      indicatorColor: palette.accentSoft,
    ),
    textTheme: base.textTheme.apply(
      bodyColor: palette.text,
      displayColor: palette.text,
    ),
    extensions: [
      ...base.extensions.values
          .where((extension) => extension is! SchoolModeColors)
          .cast<ThemeExtension<dynamic>>(),
      palette,
    ],
  );
}

SchoolDesignMode? _normalizeMode(Object? value) {
  if (value == 'informal') return SchoolDesignMode.informal;
  if (value == 'formal') return SchoolDesignMode.formal;
  return null;
}
