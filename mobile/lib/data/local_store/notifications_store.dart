/// Structured local cache for the last 100 notifications.

import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'database.dart';

class NotificationsStore {
  Future<List<Map<String, dynamic>>> readAll() async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cached_notifications',
      orderBy: 'updated_at DESC',
      limit: 100,
    );
    return rows
        .map((row) =>
            jsonDecode(row['payload'] as String) as Map<String, dynamic>)
        .toList();
  }

  Future<void> replaceAll(List<Map<String, dynamic>> notifications) async {
    final db = await AppDatabase.instance;
    final batch = db.batch();
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;

    batch.delete('cached_notifications');
    for (final item in notifications.take(100)) {
      batch.insert(
        'cached_notifications',
        {
          'notification_id': item['id'],
          'payload': jsonEncode(item),
          'created_at': now,
          'updated_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<void> upsert(Map<String, dynamic> notification) async {
    final db = await AppDatabase.instance;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    await db.insert(
      'cached_notifications',
      {
        'notification_id': notification['id'],
        'payload': jsonEncode(notification),
        'created_at': now,
        'updated_at': now,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
    await _trim(db);
  }

  Future<void> remove(String notificationId) async {
    final db = await AppDatabase.instance;
    await db.delete(
      'cached_notifications',
      where: 'notification_id = ?',
      whereArgs: [notificationId],
    );
  }

  Future<void> _trim(Database db) async {
    final rows = await db.query(
      'cached_notifications',
      columns: ['notification_id'],
      orderBy: 'updated_at DESC',
      offset: 100,
    );
    if (rows.isEmpty) return;
    final ids =
        rows.map((row) => row['notification_id']).whereType<String>().toList();
    final placeholders = List.filled(ids.length, '?').join(', ');
    await db.delete(
      'cached_notifications',
      where: 'notification_id IN ($placeholders)',
      whereArgs: ids,
    );
  }
}
