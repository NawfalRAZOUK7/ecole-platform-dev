/// Tests for lib/domain/common/pagination.dart
///
/// Covers:
///   - Construction with all required fields
///   - hasMore flag semantics
///   - Optional nextCursor handling
///   - Empty list edge case
///   - Strongly typed item lists

import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/domain/common/pagination.dart';

void main() {
  group('PaginatedList', () {
    test('constructs with items, cursor, and hasMore', () {
      const page = PaginatedList<int>(
        items: [1, 2, 3],
        nextCursor: 'next-token',
        hasMore: true,
      );

      expect(page.items, [1, 2, 3]);
      expect(page.nextCursor, 'next-token');
      expect(page.hasMore, isTrue);
    });

    test('supports an empty result set with hasMore=false and null cursor', () {
      const page = PaginatedList<String>(
        items: [],
        hasMore: false,
      );

      expect(page.items, isEmpty);
      expect(page.nextCursor, isNull);
      expect(page.hasMore, isFalse);
    });

    test('hasMore=true with no cursor is allowed (caller-defined contract)', () {
      const page = PaginatedList<String>(
        items: ['a'],
        hasMore: true,
        // nextCursor intentionally omitted
      );

      expect(page.hasMore, isTrue);
      expect(page.nextCursor, isNull);
    });

    test('is strongly typed in the item parameter', () {
      const intPage = PaginatedList<int>(items: [1], hasMore: false);
      const stringPage = PaginatedList<String>(items: ['a'], hasMore: false);

      expect(intPage.items.first, isA<int>());
      expect(stringPage.items.first, isA<String>());
    });

    test('preserves item order', () {
      const page = PaginatedList<String>(
        items: ['z', 'a', 'm'],
        hasMore: false,
      );

      expect(page.items, ['z', 'a', 'm']);
    });
  });
}
