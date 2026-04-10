import 'package:flutter/material.dart';

enum AppDialogVariant { neutral, danger }

class AppConfirmDialog {
  const AppConfirmDialog._();

  static Future<bool> show(
    BuildContext context, {
    required String title,
    required String message,
    String confirmLabel = 'Confirm',
    String cancelLabel = 'Cancel',
    AppDialogVariant variant = AppDialogVariant.neutral,
    Future<void> Function()? onConfirm,
  }) async {
    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        final theme = Theme.of(dialogContext);
        final confirmStyle = variant == AppDialogVariant.danger
            ? FilledButton.styleFrom(
                backgroundColor: theme.colorScheme.error,
                foregroundColor: theme.colorScheme.onError,
              )
            : null;

        return AlertDialog(
          title: Text(title),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(false),
              child: Text(cancelLabel),
            ),
            FilledButton(
              style: confirmStyle,
              onPressed: () async {
                await onConfirm?.call();
                if (dialogContext.mounted) {
                  Navigator.of(dialogContext).pop(true);
                }
              },
              child: Text(confirmLabel),
            ),
          ],
        );
      },
    );

    return result ?? false;
  }
}
