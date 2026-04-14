import 'package:flutter/material.dart';

class AppColors {
  const AppColors._();

  // Light theme colors
  static const primary = Color(0xFF2563EB);
  static const primaryLight = Color(0xFF93C5FD);
  static const primaryDark = Color(0xFF1E40AF);
  static const secondary = Color(0xFF7C3AED);
  static const accent = Color(0xFFF59E0B);
  static const success = Color(0xFF4CAF50);
  static const warning = Color(0xFFFF9800);
  static const error = Color(0xFFEF4444);
  static const info = Color(0xFF2196F3);
  static const background = Color(0xFFFFFFFF);
  static const surface = Color(0xFFF9FAFB);
  static const border = Color(0xFFE5E7EB);
  static const text = Color(0xFF1F2937);
  static const textSecondary = Color(0xFF6B7280);
  static const successContainer = Color(0xFFDCFCE7);
  static const warningContainer = Color(0xFFFEF3C7);
  static const infoContainer = Color(0xFFDBEAFE);
  static const chartPalette = <Color>[
    success,
    warning,
    error,
    info,
    secondary,
    primary,
    Color(0xFF8B5CF6),
    Color(0xFF14B8A6),
  ];
  static const subjectColors = <String, Color>{
    'math': Color(0xFFEFF6FF),
    'french': Color(0xFFFEF3C7),
    'arabic': Color(0xFFECFDF5),
    'science': Color(0xFFF0FDF4),
    'history': Color(0xFFFAF5FF),
    'geography': Color(0xFFFFF7ED),
    'english': Color(0xFFFDF2F8),
    'islamic_studies': Color(0xFFF0F9FF),
    'art': Color(0xFFFEFCE8),
    'sport': Color(0xFFF0FDFA),
    'default': Color(0xFFF3F4F6),
  };

  // Dark theme colors
  static const darkPrimary = Color(0xFF6B8AFF);
  static const darkSecondary = Color(0xFFA78BFA);
  static const darkSuccess = Color(0xFF34D399);
  static const darkSuccessContainer = Color(0xFF14532D);
  static const darkWarning = Color(0xFFFBBF24);
  static const darkWarningContainer = Color(0xFF78350F);
  static const darkInfo = Color(0xFF60A5FA);
  static const darkInfoContainer = Color(0xFF1E3A8A);
  static const darkBackground = Color(0xFF0F172A);
  static const darkSurface = Color(0xFF1E293B);
  static const darkBorder = Color(0xFF334155);
  static const darkText = Color(0xFFF1F5F9);
  static const darkTextSecondary = Color(0xFF94A3B8);
  static const darkChartPalette = <Color>[
    darkSuccess,
    darkWarning,
    error,
    darkInfo,
    darkSecondary,
    darkPrimary,
    Color(0xFFC084FC),
    Color(0xFF2DD4BF),
  ];
  static const darkSubjectColors = <String, Color>{
    'math': Color(0xFF1E3A8A),
    'french': Color(0xFF78350F),
    'arabic': Color(0xFF14532D),
    'science': Color(0xFF166534),
    'history': Color(0xFF581C87),
    'geography': Color(0xFF7C2D12),
    'english': Color(0xFF831843),
    'islamic_studies': Color(0xFF0C4A6E),
    'art': Color(0xFF713F12),
    'sport': Color(0xFF134E4A),
    'default': Color(0xFF334155),
  };
}

@immutable
class AppThemeColors extends ThemeExtension<AppThemeColors> {
  final Color success;
  final Color successContainer;
  final Color warning;
  final Color warningContainer;
  final Color info;
  final Color infoContainer;
  final List<Color> chartPalette;
  final Map<String, Color> subjectColors;

  const AppThemeColors({
    required this.success,
    required this.successContainer,
    required this.warning,
    required this.warningContainer,
    required this.info,
    required this.infoContainer,
    required this.chartPalette,
    required this.subjectColors,
  });

  static const light = AppThemeColors(
    success: AppColors.success,
    successContainer: AppColors.successContainer,
    warning: AppColors.warning,
    warningContainer: AppColors.warningContainer,
    info: AppColors.info,
    infoContainer: AppColors.infoContainer,
    chartPalette: AppColors.chartPalette,
    subjectColors: AppColors.subjectColors,
  );

  static const dark = AppThemeColors(
    success: AppColors.darkSuccess,
    successContainer: AppColors.darkSuccessContainer,
    warning: AppColors.darkWarning,
    warningContainer: AppColors.darkWarningContainer,
    info: AppColors.darkInfo,
    infoContainer: AppColors.darkInfoContainer,
    chartPalette: AppColors.darkChartPalette,
    subjectColors: AppColors.darkSubjectColors,
  );

  @override
  AppThemeColors copyWith({
    Color? success,
    Color? successContainer,
    Color? warning,
    Color? warningContainer,
    Color? info,
    Color? infoContainer,
    List<Color>? chartPalette,
    Map<String, Color>? subjectColors,
  }) {
    return AppThemeColors(
      success: success ?? this.success,
      successContainer: successContainer ?? this.successContainer,
      warning: warning ?? this.warning,
      warningContainer: warningContainer ?? this.warningContainer,
      info: info ?? this.info,
      infoContainer: infoContainer ?? this.infoContainer,
      chartPalette: chartPalette ?? this.chartPalette,
      subjectColors: subjectColors ?? this.subjectColors,
    );
  }

  @override
  AppThemeColors lerp(ThemeExtension<AppThemeColors>? other, double t) {
    if (other is! AppThemeColors) {
      return this;
    }

    return AppThemeColors(
      success: Color.lerp(success, other.success, t) ?? success,
      successContainer:
          Color.lerp(successContainer, other.successContainer, t) ??
              successContainer,
      warning: Color.lerp(warning, other.warning, t) ?? warning,
      warningContainer:
          Color.lerp(warningContainer, other.warningContainer, t) ??
              warningContainer,
      info: Color.lerp(info, other.info, t) ?? info,
      infoContainer:
          Color.lerp(infoContainer, other.infoContainer, t) ?? infoContainer,
      chartPalette: t < 0.5 ? chartPalette : other.chartPalette,
      subjectColors: t < 0.5 ? subjectColors : other.subjectColors,
    );
  }
}

/// Kid-facing content colors — used in story reader, mini-games, coloring, mascot.
class KidsContentColors {
  const KidsContentColors._();

  // Story reader palette
  static const storyBackground = Color(0xFFFFF8ED);
  static const storyPageTurn = Color(0xFFFF6B35);
  static const storyText = Color(0xFF2D1B00);
  static const storyHighlight = Color(0xFFFFD93D);

  // Stars / XP reward system
  static const starGold = Color(0xFFFFD700);
  static const starSilver = Color(0xFFC0C0C0);
  static const starBronze = Color(0xFFCD7F32);
  static const xpBar = Color(0xFF4CAF50);
  static const xpBarBackground = Color(0xFFE8F5E9);
  static const levelBadge = Color(0xFF7C3AED);
  static const streakOrange = Color(0xFFFF6B35);

  // Mini-game palette
  static const gameBlue = Color(0xFF4FC3F7);
  static const gameGreen = Color(0xFF81C784);
  static const gamePurple = Color(0xFFCE93D8);
  static const gameYellow = Color(0xFFFFF176);
  static const gameRed = Color(0xFFEF9A9A);
  static const gameCardBack = Color(0xFF1565C0);

  // Coloring canvas
  static const canvasBackground = Color(0xFFFFFFFF);
  static const colorPickerBorder = Color(0xFFBBBBBB);

  // Mascot / Sami
  static const samiPrimary = Color(0xFF4CAF50);
  static const samiSecondary = Color(0xFFFFEB3B);
  static const samiBubble = Color(0xFFF0FDF4);
  static const samiBubbleBorder = Color(0xFF86EFAC);
}

extension AppThemeDataColors on ThemeData {
  AppThemeColors get semanticPalette =>
      extension<AppThemeColors>() ??
      (brightness == Brightness.dark
          ? AppThemeColors.dark
          : AppThemeColors.light);
}
