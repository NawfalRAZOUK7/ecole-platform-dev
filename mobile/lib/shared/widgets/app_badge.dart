import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/radii.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

enum AppBadgeVariant { success, warning, error, info, neutral }

class AppBadge extends StatelessWidget {
  final String label;
  final AppBadgeVariant variant;

  const AppBadge({
    super.key,
    required this.label,
    this.variant = AppBadgeVariant.neutral,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    final (background, foreground, border) = switch (variant) {
      AppBadgeVariant.success => (
          colorScheme.primaryContainer,
          colorScheme.onPrimaryContainer,
          colorScheme.primary,
        ),
      AppBadgeVariant.warning => (
          colorScheme.secondaryContainer,
          colorScheme.onSecondaryContainer,
          colorScheme.secondary,
        ),
      AppBadgeVariant.error => (
          colorScheme.errorContainer,
          colorScheme.onErrorContainer,
          colorScheme.error,
        ),
      AppBadgeVariant.info => (
          colorScheme.tertiaryContainer,
          colorScheme.onTertiaryContainer,
          colorScheme.tertiary,
        ),
      AppBadgeVariant.neutral => (
          colorScheme.surfaceContainerHighest,
          colorScheme.onSurfaceVariant,
          colorScheme.outline,
        ),
    };

    return Semantics(
      container: true,
      label: '$label badge',
      child: ExcludeSemantics(
        child: Container(
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.sm,
            vertical: AppSpacing.xs,
          ),
          decoration: BoxDecoration(
            color: background,
            borderRadius: BorderRadius.circular(AppRadii.full),
            border: Border.all(color: border),
          ),
          child: Text(
            label,
            style: theme.textTheme.labelSmall?.copyWith(
              color: foreground,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ),
    );
  }
}
