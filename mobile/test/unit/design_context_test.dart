import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/shared/ui/age_theme.dart';
import 'package:ecole_platform/shared/ui/design_context.dart';

void main() {
  group('school design context', () {
    test('defaults to formal for regular schools', () {
      expect(
        resolveSchoolDesignMode(role: 'ADM', schoolType: 'formal'),
        SchoolDesignMode.formal,
      );
    });

    test('uses settings override before school type', () {
      expect(
        resolveSchoolDesignMode(
          role: 'DIR',
          schoolType: 'formal',
          schoolSettings: {'design_mode': 'informal'},
        ),
        SchoolDesignMode.informal,
      );
    });

    test('forces informal for educator and micro routes', () {
      expect(
        resolveSchoolDesignMode(role: 'EDUCATOR', schoolType: 'formal'),
        SchoolDesignMode.informal,
      );
      expect(
        resolveSchoolDesignMode(route: '/micro-schools'),
        SchoolDesignMode.informal,
      );
    });
  });

  group('student age tier', () {
    test('resolves Moroccan class levels', () {
      expect(resolveAgeTier(niveau: 'CP'), AgeTier.primaire);
      expect(resolveAgeTier(niveau: '6eme'), AgeTier.college);
      expect(resolveAgeTier(niveau: '3AC'), AgeTier.college);
      expect(resolveAgeTier(niveau: 'Terminale'), AgeTier.college);
    });

    test('falls back to primaire when profile data is missing', () {
      expect(resolveAgeTier(), AgeTier.primaire);
    });
  });
}
