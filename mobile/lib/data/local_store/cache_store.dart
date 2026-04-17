/// TTL-based offline cache store per DEC-E2-020.
///
/// Cache policies from Pack E2 Chapter 5:
///   feed:          5 min TTL
///   notifications: 2 min TTL
///   content-items: 15 min TTL
///   results:       10 min TTL
///   invoices:      10 min TTL
///
/// Pull-to-refresh invalidates cache for the endpoint.

import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'database.dart';

/// TTL policies per endpoint (in seconds).
class CacheTtl {
  static const int feed = 5 * 60; // 5 minutes
  static const int notifications = 2 * 60; // 2 minutes
  static const int contentItems = 15 * 60; // 15 minutes
  static const int results = 10 * 60; // 10 minutes
  static const int invoices = 10 * 60; // 10 minutes
  static const int gradebook = 10 * 60; // 10 minutes
  static const int attendance = 10 * 60; // 10 minutes

  // Offline content TTLs
  static const int offlineContent = 7 * 24 * 60 * 60; // 7 days
  static const int offlineAssets = 30 * 24 * 60 * 60; // 30 days
}

class CacheStore {
  /// Get cached data if not expired.
  Future<List<Map<String, dynamic>>?> get(String key) async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cache_entries',
      where: 'cache_key = ?',
      whereArgs: [key],
    );

    if (rows.isEmpty) return null;

    final entry = rows.first;
    final createdAt = entry['created_at'] as int;
    final ttlSeconds = entry['ttl_seconds'] as int;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;

    // Check TTL
    if (now - createdAt > ttlSeconds) {
      // Expired — delete and return null
      await db
          .delete('cache_entries', where: 'cache_key = ?', whereArgs: [key]);
      return null;
    }

    final data = entry['data'] as String;
    final decoded = jsonDecode(data) as List<dynamic>;
    return decoded.cast<Map<String, dynamic>>();
  }

  /// Store data with TTL.
  Future<void> put(
      String key, List<Map<String, dynamic>> data, int ttlSeconds) async {
    final db = await AppDatabase.instance;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;

    await db.insert(
      'cache_entries',
      {
        'cache_key': key,
        'data': jsonEncode(data),
        'created_at': now,
        'ttl_seconds': ttlSeconds,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Invalidate a specific cache key (pull-to-refresh).
  Future<void> invalidate(String key) async {
    final db = await AppDatabase.instance;
    await db.delete('cache_entries', where: 'cache_key = ?', whereArgs: [key]);
  }

  /// Invalidate all cache keys matching a prefix.
  Future<void> invalidatePrefix(String prefix) async {
    final db = await AppDatabase.instance;
    await db.delete('cache_entries',
        where: 'cache_key LIKE ?', whereArgs: ['$prefix%']);
  }

  /// Clear all cached data.
  Future<void> clearAll() async {
    final db = await AppDatabase.instance;
    await db.delete('cache_entries');
  }

  /// Remove expired entries (housekeeping).
  Future<void> pruneExpired() async {
    final db = await AppDatabase.instance;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    await db.rawDelete(
      'DELETE FROM cache_entries WHERE (? - created_at) > ttl_seconds',
      [now],
    );
  }
}
