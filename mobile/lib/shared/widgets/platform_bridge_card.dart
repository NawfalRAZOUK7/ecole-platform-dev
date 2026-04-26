/// Cross-platform bridge card — informs users that a feature
/// is available on another platform (web or mobile) with an
/// attractive, branded design and a brief explanation.
///
/// Usage:
///   PlatformBridgeCard(
///     targetPlatform: TargetPlatform.web,
///     title: 'إنشاء المحتوى',
///     description: 'لإنشاء الاختبارات وتعديل المحتوى، استخدم المنصة على الحاسوب.',
///     icon: Icons.computer,
///   )

import 'package:flutter/material.dart';

import 'package:ecole_platform/shared/ui/tokens/colors.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';

enum BridgePlatform { web, mobile }

class PlatformBridgeCard extends StatelessWidget {
  final BridgePlatform targetPlatform;
  final String title;
  final String description;
  final IconData? icon;
  final TextDirection textDirection;

  const PlatformBridgeCard({
    super.key,
    required this.targetPlatform,
    required this.title,
    required this.description,
    this.icon,
    this.textDirection = TextDirection.rtl,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isWeb = targetPlatform == BridgePlatform.web;

    final Color accentColor =
        isWeb ? AppColors.primary : AppColors.secondary;
    final Color bgColor = accentColor.withAlpha(15);
    final Color borderColor = accentColor.withAlpha(60);
    final IconData platformIcon =
        icon ?? (isWeb ? Icons.computer_rounded : Icons.phone_android_rounded);
    final String platformLabel = isWeb
        ? 'متوفر على الويب'
        : 'متوفر على التطبيق';

    return Container(
      margin: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
      padding: const EdgeInsets.all(AppSpacing.base),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: borderColor, width: 1.2),
      ),
      child: Row(
        textDirection: textDirection,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Platform icon
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              color: accentColor.withAlpha(25),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: accentColor.withAlpha(50)),
            ),
            child: Icon(
              platformIcon,
              size: 28,
              color: accentColor,
            ),
          ),
          const SizedBox(width: AppSpacing.md),
          // Text content
          Expanded(
            child: Column(
              crossAxisAlignment: textDirection == TextDirection.rtl
                  ? CrossAxisAlignment.end
                  : CrossAxisAlignment.start,
              children: [
                // Platform badge
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.sm,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: accentColor.withAlpha(30),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    platformLabel,
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: accentColor,
                      fontWeight: FontWeight.w700,
                      fontSize: 11,
                    ),
                    textDirection: textDirection,
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                // Title
                Text(
                  title,
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: theme.colorScheme.onSurface,
                  ),
                  textDirection: textDirection,
                ),
                const SizedBox(height: AppSpacing.xs),
                // Description
                Text(
                  description,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.onSurfaceVariant,
                    height: 1.5,
                  ),
                  textDirection: textDirection,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
