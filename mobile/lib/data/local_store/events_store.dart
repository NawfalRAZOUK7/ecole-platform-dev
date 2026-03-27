import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'database.dart';

class EventsStore {
  Future<List<Map<String, dynamic>>> readMonth(String monthKey) async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cached_calendar_events',
      where: 'cache_month = ?',
      whereArgs: [monthKey],
      orderBy: 'start_at ASC, updated_at DESC',
    );
    return rows
        .map((row) =>
            jsonDecode(row['payload'] as String) as Map<String, dynamic>)
        .toList();
  }

  Future<void> replaceMonth(
      String monthKey, List<Map<String, dynamic>> events) async {
    final db = await AppDatabase.instance;
    final batch = db.batch();
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;

    batch.delete(
      'cached_calendar_events',
      where: 'cache_month = ?',
      whereArgs: [monthKey],
    );

    for (final event in events) {
      batch.insert(
        'cached_calendar_events',
        {
          'cache_month': monthKey,
          'event_id': event['instance_id'] ?? event['id'],
          'payload': jsonEncode(event),
          'start_at': event['start_at'],
          'updated_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);
    await _trim(db);
  }

  Future<void> _trim(Database db) async {
    final rows = await db.rawQuery('''
      SELECT cache_month
      FROM cached_calendar_events
      GROUP BY cache_month
      ORDER BY MAX(updated_at) DESC
      LIMIT -1 OFFSET 3
    ''');
    if (rows.isEmpty) return;
    final months =
        rows.map((row) => row['cache_month']).whereType<String>().toList();
    final placeholders = List.filled(months.length, '?').join(', ');
    await db.delete(
      'cached_calendar_events',
      where: 'cache_month IN ($placeholders)',
      whereArgs: months,
    );
  }
}
