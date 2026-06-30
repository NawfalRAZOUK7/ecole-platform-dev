import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/presentation/shell_screen.dart';
import 'package:ecole_platform/shared/ui/tokens/colors.dart';

void main() {
  group('role navigation', () {
    test('keeps primary destinations compact and exposes secondary routes', () {
      for (final role in ['ADM', 'DIR', 'TCH', 'PAR', 'STD']) {
        final primaryRoutes = primaryNavigationRoutesForRole(role);
        final secondaryRoutes = secondaryNavigationRoutesForRole(role);

        expect(primaryRoutes, hasLength(lessThanOrEqualTo(4)));
        expect(secondaryRoutes, isNotEmpty);
      }
    });

    test('uses demo-ready primary routes for each role', () {
      expect(
        primaryNavigationRoutesForRole('ADM'),
        ['/admin/dashboard', '/admin/users', '/analytics', '/budgets'],
      );
      expect(
        primaryNavigationRoutesForRole('DIR'),
        ['/admin/dashboard', '/analytics', '/budgets', '/reports'],
      );
      expect(
        primaryNavigationRoutesForRole('TCH'),
        [
          '/teacher/classes',
          '/teacher/content-library',
          '/teacher/submissions',
          '/teacher/class-progress',
        ],
      );
      expect(
        primaryNavigationRoutesForRole('PAR'),
        ['/family', '/grades', '/invoices', '/messages'],
      );
      expect(
        primaryNavigationRoutesForRole('STD'),
        ['/student/home', '/student/content', '/student/quizzes', '/progress'],
      );
    });

    test('uses shared design token values for web/mobile parity', () {
      expect(AppColors.primaryLight, const Color(0xFF60A5FA));
      expect(AppColors.primaryDark, const Color(0xFF1D4ED8));
      expect(AppColors.secondary, const Color(0xFF8B5CF6));
      expect(AppColors.success, const Color(0xFF10B981));
      expect(AppColors.warning, const Color(0xFFF59E0B));
      expect(AppColors.info, const Color(0xFF0EA5E9));
      expect(AppColors.background, const Color(0xFFF9FAFB));
      expect(AppColors.surface, const Color(0xFFFFFFFF));
      expect(AppColors.text, const Color(0xFF111827));
    });
  });
}
