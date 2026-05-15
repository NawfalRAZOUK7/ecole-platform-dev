/// Structured local cache for the last 5 generated reports.

import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'database.dart';

class ReportsStore {
  Future<List<Map<String, dynamic>>> readAll() async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cached_reports',
      orderBy: 'updated_at DESC',
      limit: 5,
    );
    return rows.map((row) {
      final payload =
          jsonDecode(row['payload'] as String) as Map<String, dynamic>;
      payload['local_file_path'] = row['file_path'];
      return payload;
    }).toList();
  }

  Future<Map<String, dynamic>?> readById(String reportJobId) async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cached_reports',
      where: 'report_job_id = ?',
      whereArgs: [reportJobId],
      limit: 1,
    );
    if (rows.isEmpty) return null;
    final payload =
        jsonDecode(rows.first['payload'] as String) as Map<String, dynamic>;
    payload['local_file_path'] = rows.first['file_path'];
    return payload;
  }

  Future<void> upsert(
    Map<String, dynamic> report, {
    String? filePath,
  }) async {
    final db = await AppDatabase.instance;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    await db.insert(
      'cached_reports',
      {
        'report_job_id': report['id'],
        'payload': jsonEncode(report),
        'file_path': filePath ?? report['local_file_path'],
        'created_at': now,
        'updated_at': now,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
    await _trim(db);
  }

  Future<void> _trim(Database db) async {
    final rows = await db.query(
      'cached_reports',
      columns: ['report_job_id'],
      orderBy: 'updated_at DESC',
      offset: 5,
    );
    if (rows.isEmpty) return;
    final ids =
        rows.map((row) => row['report_job_id']).whereType<String>().toList();
    final placeholders = List.filled(ids.length, '?').join(', ');
    await db.delete(
      'cached_reports',
      where: 'report_job_id IN ($placeholders)',
      whereArgs: ids,
    );
  }
}
