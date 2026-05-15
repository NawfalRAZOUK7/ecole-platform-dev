import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/radii.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/ui/tokens/typography.dart';

final ThemeData appDarkTheme = ThemeData(
  brightness: Brightness.dark,
  colorScheme: ColorScheme.fromSeed(
    seedColor: AppColors.darkPrimary,
    brightness: Brightness.dark,
    primary: AppColors.darkPrimary,
    secondary: AppColors.darkSecondary,
    tertiary: AppColors.darkInfo,
    surface: AppColors.darkSurface,
    error: AppColors.error,
  ),
  extensions: const <ThemeExtension<dynamic>>[
    AppThemeColors.dark,
  ],
  useMaterial3: true,
  fontFamily: 'Cairo',
  scaffoldBackgroundColor: AppColors.darkBackground,
  appBarTheme: const AppBarTheme(
    centerTitle: true,
    elevation: 0,
    backgroundColor: AppColors.darkBackground,
    foregroundColor: AppColors.darkText,
    surfaceTintColor: Colors.transparent,
    titleTextStyle: TextStyle(
      color: AppColors.darkText,
      fontSize: 20,
      fontWeight: FontWeight.w600,
      fontFamily: 'Cairo',
    ),
  ),
  cardTheme: CardThemeData(
    elevation: 1,
    color: AppColors.darkSurface,
    shadowColor: Colors.black.withValues(alpha: 0.25),
    surfaceTintColor: Colors.transparent,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(AppRadii.lg),
      side: const BorderSide(color: AppColors.darkBorder),
    ),
    margin: const EdgeInsets.all(AppSpacing.sm),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: AppColors.darkSurface,
    contentPadding: const EdgeInsets.symmetric(
      horizontal: AppSpacing.base,
      vertical: AppSpacing.md,
    ),
    labelStyle:
        AppTypography.label.copyWith(color: AppColors.darkTextSecondary),
    hintStyle:
        AppTypography.bodySmall.copyWith(color: AppColors.darkTextSecondary),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(AppRadii.md),
      borderSide: const BorderSide(color: AppColors.darkBorder),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(AppRadii.md),
      borderSide: const BorderSide(color: AppColors.darkPrimary, width: 1.4),
    ),
    errorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(AppRadii.md),
      borderSide: const BorderSide(color: AppColors.error),
    ),
    focusedErrorBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(AppRadii.md),
      borderSide: const BorderSide(color: AppColors.error, width: 1.4),
    ),
  ),
  dividerTheme: const DividerThemeData(
    color: AppColors.darkBorder,
    thickness: 1,
    space: AppSpacing.lg,
  ),
  chipTheme: ChipThemeData(
    backgroundColor: AppColors.darkSurface,
    selectedColor: AppColors.darkPrimary.withAlpha(48),
    labelStyle: AppTypography.label.copyWith(color: AppColors.darkText),
    padding: const EdgeInsets.symmetric(
      horizontal: AppSpacing.sm,
      vertical: AppSpacing.xs,
    ),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(AppRadii.full),
      side: const BorderSide(color: AppColors.darkBorder),
    ),
  ),
  navigationBarTheme: NavigationBarThemeData(
    backgroundColor: AppColors.darkSurface,
    indicatorColor: AppColors.darkPrimary.withAlpha(48),
    labelTextStyle: WidgetStateProperty.resolveWith(
      (states) => AppTypography.caption.copyWith(
        color: states.contains(WidgetState.selected)
            ? AppColors.darkText
            : AppColors.darkTextSecondary,
      ),
    ),
  ),
  textTheme: TextTheme(
    displayLarge: AppTypography.heading1.copyWith(color: AppColors.darkText),
    displayMedium: AppTypography.heading2.copyWith(color: AppColors.darkText),
    titleLarge: AppTypography.heading3.copyWith(color: AppColors.darkText),
    titleMedium: AppTypography.heading4.copyWith(color: AppColors.darkText),
    bodyLarge: AppTypography.body.copyWith(color: AppColors.darkText),
    bodyMedium: AppTypography.bodySmall.copyWith(color: AppColors.darkText),
    bodySmall:
        AppTypography.caption.copyWith(color: AppColors.darkTextSecondary),
    labelLarge: AppTypography.label.copyWith(color: AppColors.darkText),
  ),
);
