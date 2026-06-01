/// Tests for lib/domain/entities/user/child_link.dart
///
/// Covers:
///   - Required field construction
///   - Optional fields default to null
///   - classLevel getter reads from studentProfile map
///   - classLevel returns null when profile is absent or key is missing

import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/domain/entities/user/child_link.dart';

void main() {
  group('ChildLink', () {
    test('constructs with all required fields', () {
      const link = ChildLink(
        userId: 'u-1',
        fullName: 'Yassine Alaoui',
        linkId: 'link-1',
      );

      expect(link.userId, 'u-1');
      expect(link.fullName, 'Yassine Alaoui');
      expect(link.linkId, 'link-1');
      expect(link.email, isNull);
      expect(link.linkedAt, isNull);
      expect(link.studentProfile, isNull);
    });

    test('holds optional email and linkedAt fields', () {
      const link = ChildLink(
        userId: 'u-1',
        fullName: 'Yassine Alaoui',
        email: 'yassine@example.test',
        linkId: 'link-1',
        linkedAt: '2026-01-15T10:00:00Z',
      );

      expect(link.email, 'yassine@example.test');
      expect(link.linkedAt, '2026-01-15T10:00:00Z');
    });

    test('classLevel reads class_level from studentProfile map', () {
      const link = ChildLink(
        userId: 'u-1',
        fullName: 'Test',
        linkId: 'link-1',
        studentProfile: {'class_level': 'CP', 'other_field': 1},
      );

      expect(link.classLevel, 'CP');
    });

    test('classLevel returns null when studentProfile is null', () {
      const link = ChildLink(
        userId: 'u-1',
        fullName: 'Test',
        linkId: 'link-1',
      );

      expect(link.classLevel, isNull);
    });

    test('classLevel returns null when class_level key is missing', () {
      const link = ChildLink(
        userId: 'u-1',
        fullName: 'Test',
        linkId: 'link-1',
        studentProfile: {'other_field': 'something'},
      );

      expect(link.classLevel, isNull);
    });

    test('classLevel throws a TypeError when class_level value is not a string', () {
      // Production code uses `as String?`, which throws TypeError on non-string
      // non-null values (Dart strict typing). This test documents that contract:
      // callers of ChildLink.classLevel must trust the upstream API to always
      // emit class_level as a string (or null).
      const link = ChildLink(
        userId: 'u-1',
        fullName: 'Test',
        linkId: 'link-1',
        studentProfile: {'class_level': 42},
      );

      expect(() => link.classLevel, throwsA(isA<TypeError>()));
    });
  });
}
