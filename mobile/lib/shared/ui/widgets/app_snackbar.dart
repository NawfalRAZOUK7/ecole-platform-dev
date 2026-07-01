/// Consistent, variant-styled snackbars.
///
/// Replaces ad-hoc `ScaffoldMessenger.showSnackBar(SnackBar(content: Text(...)))`
/// calls with a single helper that applies floating behaviour, rounded corners,
/// an icon and semantic colours per variant — matching the web toast language.
/// Existing snackbars stay valid; adopt this incrementally.

import 'package:flutter/material.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

enum SnackVariant { info, success, error }

class AppSnackBar {
  AppSnackBar._();

  static void show(
    BuildContext context,
    String message, {
    SnackVariant variant = SnackVariant.info,
  }) {
    final theme = Theme.of(context);

    Color background;
    Color foreground;
    IconData icon;
    if (variant == SnackVariant.success) {
      background = theme.semanticPalette.success;
      foreground = Colors.white;
      icon = Icons.check_circle_outline;
    } else if (variant == SnackVariant.error) {
      background = theme.colorScheme.error;
      foreground = theme.colorScheme.onError;
      icon = Icons.error_outline;
    } else {
      background = theme.colorScheme.inverseSurface;
      foreground = theme.colorScheme.onInverseSurface;
      icon = Icons.info_outline;
    }

    final messenger = ScaffoldMessenger.of(context);
    messenger.clearSnackBars();
    messenger.showSnackBar(
      SnackBar(
        behavior: SnackBarBehavior.floating,
        backgroundColor: background,
        duration: const Duration(seconds: 3),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        content: Row(
          children: [
            Icon(icon, color: foreground, size: 20),
            const SizedBox(width: 12),
            Expanded(
              child: Text(message, style: TextStyle(color: foreground)),
            ),
          ],
        ),
      ),
    );
  }

  static void success(BuildContext context, String message) =>
      show(context, message, variant: SnackVariant.success);

  static void error(BuildContext context, String message) =>
      show(context, message, variant: SnackVariant.error);
}
