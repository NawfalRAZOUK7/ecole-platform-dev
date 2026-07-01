import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/shared/ui/tokens/radii.dart';
import 'package:ecole_platform/shared/ui/tokens/spacing.dart';
import 'package:ecole_platform/shared/ui/tokens/typography.dart';

void main() {
  group('AppRadii', () {
    test('sm is 4', () => expect(AppRadii.sm, 4.0));
    test('md is 8', () => expect(AppRadii.md, 8.0));
    test('lg is 12', () => expect(AppRadii.lg, 12.0));
    test('xl is 16', () => expect(AppRadii.xl, 16.0));
    test('full is 999', () => expect(AppRadii.full, 999.0));
    test('radii increase sm < md < lg < xl < full', () {
      expect(AppRadii.sm, lessThan(AppRadii.md));
      expect(AppRadii.md, lessThan(AppRadii.lg));
      expect(AppRadii.lg, lessThan(AppRadii.xl));
      expect(AppRadii.xl, lessThan(AppRadii.full));
    });
  });

  group('AppSpacing', () {
    test('xs is 4', () => expect(AppSpacing.xs, 4.0));
    test('sm is 8', () => expect(AppSpacing.sm, 8.0));
    test('md is 12', () => expect(AppSpacing.md, 12.0));
    test('base is 16', () => expect(AppSpacing.base, 16.0));
    test('lg is 24', () => expect(AppSpacing.lg, 24.0));
    test('xl is 32', () => expect(AppSpacing.xl, 32.0));
    test('xxl is 48', () => expect(AppSpacing.xxl, 48.0));
    test('spacing increases xs < sm < md < base < lg < xl < xxl', () {
      expect(AppSpacing.xs, lessThan(AppSpacing.sm));
      expect(AppSpacing.sm, lessThan(AppSpacing.md));
      expect(AppSpacing.md, lessThan(AppSpacing.base));
      expect(AppSpacing.base, lessThan(AppSpacing.lg));
      expect(AppSpacing.lg, lessThan(AppSpacing.xl));
      expect(AppSpacing.xl, lessThan(AppSpacing.xxl));
    });
  });

  group('AppTypography', () {
    test('heading1 has fontSize 28 and bold weight', () {
      expect(AppTypography.heading1.fontSize, 28.0);
      expect(AppTypography.heading1.fontWeight, FontWeight.bold);
      expect(AppTypography.heading1.fontFamily, 'Cairo');
    });

    test('heading2 has fontSize 24', () {
      expect(AppTypography.heading2.fontSize, 24.0);
    });

    test('heading3 has fontSize 20 and w600', () {
      expect(AppTypography.heading3.fontSize, 20.0);
      expect(AppTypography.heading3.fontWeight, FontWeight.w600);
    });

    test('heading4 has fontSize 18', () {
      expect(AppTypography.heading4.fontSize, 18.0);
    });

    test('body has fontSize 16 and normal weight', () {
      expect(AppTypography.body.fontSize, 16.0);
      expect(AppTypography.body.fontWeight, FontWeight.normal);
    });

    test('bodySmall has fontSize 14', () {
      expect(AppTypography.bodySmall.fontSize, 14.0);
    });

    test('caption has fontSize 12', () {
      expect(AppTypography.caption.fontSize, 12.0);
    });

    test('label has fontSize 14 and w500', () {
      expect(AppTypography.label.fontSize, 14.0);
      expect(AppTypography.label.fontWeight, FontWeight.w500);
    });

    test('headings decrease in size h1 > h2 > h3 > h4', () {
      expect(
        AppTypography.heading1.fontSize,
        greaterThan(AppTypography.heading2.fontSize!),
      );
      expect(
        AppTypography.heading2.fontSize,
        greaterThan(AppTypography.heading3.fontSize!),
      );
      expect(
        AppTypography.heading3.fontSize,
        greaterThan(AppTypography.heading4.fontSize!),
      );
    });
  });
}
