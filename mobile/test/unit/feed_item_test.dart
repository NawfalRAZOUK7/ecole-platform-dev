/// Tests for lib/domain/entities/content/feed_item.dart
///
/// Covers:
///   - Required field construction
///   - Optional studentId, sourceRef, body
///   - Different source types preserved verbatim
///   - createdAt is just a string carrier (no parsing)

import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/domain/entities/content/feed_item.dart';

void main() {
  group('FeedItem', () {
    test('constructs with all required fields', () {
      const item = FeedItem(
        id: 'feed-1',
        schoolId: 's-1',
        parentId: 'parent-1',
        sourceType: 'announcement',
        title: 'Rentrée scolaire',
        createdAt: '2026-09-01T08:00:00Z',
      );

      expect(item.id, 'feed-1');
      expect(item.schoolId, 's-1');
      expect(item.parentId, 'parent-1');
      expect(item.sourceType, 'announcement');
      expect(item.title, 'Rentrée scolaire');
      expect(item.createdAt, '2026-09-01T08:00:00Z');

      // Optional fields default to null
      expect(item.studentId, isNull);
      expect(item.sourceRef, isNull);
      expect(item.body, isNull);
    });

    test('holds the optional studentId for student-scoped feed entries', () {
      const item = FeedItem(
        id: 'feed-2',
        schoolId: 's-1',
        parentId: 'parent-1',
        studentId: 'student-1',
        sourceType: 'grade',
        sourceRef: 'assignment-1',
        title: 'Note publiée',
        body: 'Mathématiques : 17/20',
        createdAt: '2026-04-15T12:30:00Z',
      );

      expect(item.studentId, 'student-1');
      expect(item.sourceRef, 'assignment-1');
      expect(item.body, 'Mathématiques : 17/20');
    });

    test('preserves arbitrary source types verbatim (no enum coercion)', () {
      const a = FeedItem(
        id: 'a',
        schoolId: 's',
        parentId: 'p',
        sourceType: 'announcement',
        title: 't',
        createdAt: 'now',
      );
      const b = FeedItem(
        id: 'b',
        schoolId: 's',
        parentId: 'p',
        sourceType: 'grade',
        title: 't',
        createdAt: 'now',
      );
      const c = FeedItem(
        id: 'c',
        schoolId: 's',
        parentId: 'p',
        sourceType: 'attendance',
        title: 't',
        createdAt: 'now',
      );

      expect(a.sourceType, 'announcement');
      expect(b.sourceType, 'grade');
      expect(c.sourceType, 'attendance');
    });

    test('createdAt is stored as a plain string (no parsing)', () {
      const item = FeedItem(
        id: 'f',
        schoolId: 's',
        parentId: 'p',
        sourceType: 'announcement',
        title: 't',
        createdAt: 'not-a-real-iso-date',
      );

      expect(item.createdAt, 'not-a-real-iso-date');
    });
  });
}
