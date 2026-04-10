import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

enum TrendDirection { up, down, flat }

class AppStatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData? icon;
  final TrendDirection? trend;
  final double? trendValue;

  const AppStatCard({
    super.key,
    required this.label,
    required this.value,
    this.icon,
    this.trend,
    this.trendValue,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final trendMeta = _trendMeta(theme);
    final semanticsLabel = StringBuffer()
      ..write(label)
      ..write(', ')
      ..write(value);
    if (trendMeta != null && trendValue != null) {
      semanticsLabel
        ..write(', trend ')
        ..write(trend == TrendDirection.down ? 'down ' : 'up ')
        ..write('${trendValue!.toStringAsFixed(1)} percent');
    }

    return Semantics(
      container: true,
      label: semanticsLabel.toString(),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.base),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  if (icon != null) ...[
                    Icon(icon, color: theme.colorScheme.primary),
                    const SizedBox(width: AppSpacing.sm),
                  ],
                  Expanded(
                    child: Text(label, style: theme.textTheme.labelLarge),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.base),
              Text(
                value,
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
              if (trendMeta != null && trendValue != null) ...[
                const SizedBox(height: AppSpacing.sm),
                Row(
                  children: [
                    Icon(trendMeta.icon, size: 18, color: trendMeta.color),
                    const SizedBox(width: AppSpacing.xs),
                    Text(
                      '${trendValue!.toStringAsFixed(1)}%',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: trendMeta.color,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  _TrendMeta? _trendMeta(ThemeData theme) {
    return switch (trend) {
      TrendDirection.up => _TrendMeta(
          icon: Icons.trending_up,
          color: theme.colorScheme.primary,
        ),
      TrendDirection.down => _TrendMeta(
          icon: Icons.trending_down,
          color: theme.colorScheme.error,
        ),
      TrendDirection.flat => _TrendMeta(
          icon: Icons.trending_flat,
          color: theme.colorScheme.outline,
        ),
      null => null,
    };
  }
}

class _TrendMeta {
  final IconData icon;
  final Color color;

  const _TrendMeta({
    required this.icon,
    required this.color,
  });
}
