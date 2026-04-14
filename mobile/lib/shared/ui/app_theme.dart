import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/radii.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/ui/tokens/typography.dart';

final ThemeData appLightTheme = ThemeData(
  colorScheme: ColorScheme.fromSeed(
    seedColor: AppColors.primary,
    brightness: Brightness.light,
    primary: AppColors.primary,
    secondary: AppColors.secondary,
    tertiary: AppColors.info,
    surface: AppColors.surface,
    error: AppColors.error,
  ),
  extensions: const <ThemeExtension<dynamic>>[
    AppThemeColors.light,
  ],
  useMaterial3: true,
  fontFamily: 'Cairo',
  scaffoldBackgroundColor: AppColors.background,
  appBarTheme: const AppBarTheme(
    centerTitle: true,
    elevation: 0,
    backgroundColor: AppColors.background,
    foregroundColor: AppColors.text,
    surfaceTintColor: Colors.transparent,
    titleTextStyle: TextStyle(
      color: AppColors.text,
      fontSize: 20,
      fontWeight: FontWeight.w600,
      fontFamily: 'Cairo',
    ),
  ),
  cardTheme: CardThemeData(
    elevation: 0,
    color: AppColors.background,
    surfaceTintColor: Colors.transparent,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(AppRadii.lg),
      side: const BorderSide(color: AppColors.border),
    ),
    margin: const EdgeInsets.all(AppSpacing.sm),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: AppColors.surface,
    contentPadding: const EdgeInsets.symmetric(
      horizontal: AppSpacing.base,
      vertical: AppSpacing.md,
    ),
    labelStyle: AppTypography.label.copyWith(color: AppColors.textSecondary),
    hintStyle: AppTypography.bodySmall.copyWith(color: AppColors.textSecondary),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(AppRadii.md),
      borderSide: const BorderSide(color: AppColors.border),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(AppRadii.md),
      borderSide: const BorderSide(color: AppColors.primary, width: 1.4),
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
    color: AppColors.border,
    thickness: 1,
    space: AppSpacing.lg,
  ),
  chipTheme: ChipThemeData(
    backgroundColor: AppColors.surface,
    selectedColor: AppColors.primaryLight,
    labelStyle: AppTypography.label.copyWith(color: AppColors.text),
    padding: const EdgeInsets.symmetric(
      horizontal: AppSpacing.sm,
      vertical: AppSpacing.xs,
    ),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(AppRadii.full),
      side: const BorderSide(color: AppColors.border),
    ),
  ),
  navigationBarTheme: NavigationBarThemeData(
    backgroundColor: AppColors.background,
    indicatorColor: AppColors.primaryLight,
    labelTextStyle: WidgetStateProperty.resolveWith(
      (states) => AppTypography.caption.copyWith(
        color: states.contains(WidgetState.selected)
            ? AppColors.primaryDark
            : AppColors.textSecondary,
      ),
    ),
  ),
  textTheme: TextTheme(
    displayLarge: AppTypography.heading1.copyWith(color: AppColors.text),
    displayMedium: AppTypography.heading2.copyWith(color: AppColors.text),
    titleLarge: AppTypography.heading3.copyWith(color: AppColors.text),
    titleMedium: AppTypography.heading4.copyWith(color: AppColors.text),
    bodyLarge: AppTypography.body.copyWith(color: AppColors.text),
    bodyMedium: AppTypography.bodySmall.copyWith(color: AppColors.text),
    bodySmall: AppTypography.caption.copyWith(color: AppColors.textSecondary),
    labelLarge: AppTypography.label.copyWith(color: AppColors.text),
  ),
);
