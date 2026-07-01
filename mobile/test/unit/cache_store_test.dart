import 'package:flutter_test/flutter_test.dart';

import 'package:ecole_platform/core/storage/cache_store.dart';
import 'package:ecole_platform/core/storage/database.dart';

import '../helpers/test_database.dart';

void main() {
  setUpAll(initializeTestDatabase);

  setUp(resetTestDatabase);

  test('writes and reads back cached records before expiry', () async {
    final store = CacheStore();

    await store.put(
      'grades:first',
      const [
        {'id': 'grade-1', 'score': 18},
      ],
      CacheTtl.gradebook,
    );

    final cached = await store.get('grades:first');

    expect(cached, isNotNull);
    expect(cached!.single['score'], 18);
  });

  test('invalidates individual cache keys', () async {
    final store = CacheStore();

    await store.put(
      'results:first',
      const [
        {'id': 'result-1'},
      ],
      CacheTtl.results,
    );
    await store.invalidate('results:first');

    expect(await store.get('results:first'), isNull);
  });

  test('expires entries when max age has elapsed', () async {
    final store = CacheStore();
    final db = await AppDatabase.instance;

    await store.put(
      'feed:stale',
      const [
        {'id': 'feed-1'},
      ],
      1,
    );
    await db.update(
      'cache_entries',
      {'created_at': 0},
      where: 'cache_key = ?',
      whereArgs: ['feed:stale'],
    );

    expect(await store.get('feed:stale'), isNull);
  });
}
