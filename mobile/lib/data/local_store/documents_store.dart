import 'dart:convert';

import 'package:sqflite/sqflite.dart';

import 'database.dart';

class DocumentsStore {
  Future<List<Map<String, dynamic>>> readDocuments(String scopeKey) async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cached_documents',
      where: 'scope_key = ?',
      whereArgs: [scopeKey],
      orderBy: 'updated_at DESC, created_at DESC',
    );
    return rows.map((row) {
      final payload =
          jsonDecode(row['payload'] as String) as Map<String, dynamic>;
      payload['local_file_path'] = row['local_file_path'];
      return payload;
    }).toList();
  }

  Future<void> replaceDocuments(
    String scopeKey,
    List<Map<String, dynamic>> documents,
  ) async {
    final db = await AppDatabase.instance;
    final batch = db.batch();
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;

    batch.delete(
      'cached_documents',
      where: 'scope_key = ?',
      whereArgs: [scopeKey],
    );

    for (final document in documents) {
      batch.insert(
        'cached_documents',
        {
          'scope_key': scopeKey,
          'document_id': document['id'],
          'payload': jsonEncode(document),
          'local_file_path': document['local_file_path'],
          'created_at': now,
          'updated_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);
    await _trimDocuments(db);
  }

  Future<void> attachDocumentFile(String documentId, String filePath) async {
    final db = await AppDatabase.instance;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    await db.update(
      'cached_documents',
      {
        'local_file_path': filePath,
        'updated_at': now,
      },
      where: 'document_id = ?',
      whereArgs: [documentId],
    );
  }

  Future<List<Map<String, dynamic>>> readChecklist(String studentId) async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cached_student_document_checklists',
      where: 'student_id = ?',
      whereArgs: [studentId],
      orderBy: 'category ASC',
    );
    return rows
        .map((row) =>
            jsonDecode(row['payload'] as String) as Map<String, dynamic>)
        .toList();
  }

  Future<void> replaceChecklist(
    String studentId,
    List<Map<String, dynamic>> items,
  ) async {
    final db = await AppDatabase.instance;
    final batch = db.batch();
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    batch.delete(
      'cached_student_document_checklists',
      where: 'student_id = ?',
      whereArgs: [studentId],
    );
    for (final item in items) {
      batch.insert(
        'cached_student_document_checklists',
        {
          'student_id': studentId,
          'category': item['category'],
          'payload': jsonEncode(item),
          'updated_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<List<Map<String, dynamic>>> readResources(String scopeKey) async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cached_resources',
      where: 'scope_key = ?',
      whereArgs: [scopeKey],
      orderBy: 'updated_at DESC, created_at DESC',
    );
    return rows.map((row) {
      final payload =
          jsonDecode(row['payload'] as String) as Map<String, dynamic>;
      payload['local_file_path'] = row['local_file_path'];
      return payload;
    }).toList();
  }

  Future<void> replaceResources(
    String scopeKey,
    List<Map<String, dynamic>> resources,
  ) async {
    final db = await AppDatabase.instance;
    final batch = db.batch();
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;

    batch.delete(
      'cached_resources',
      where: 'scope_key = ?',
      whereArgs: [scopeKey],
    );

    for (final resource in resources) {
      batch.insert(
        'cached_resources',
        {
          'scope_key': scopeKey,
          'resource_id': resource['id'],
          'payload': jsonEncode(resource),
          'local_file_path': resource['local_file_path'],
          'created_at': now,
          'updated_at': now,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }

    await batch.commit(noResult: true);
    await _trimResources(db);
  }

  Future<void> attachResourceFile(String resourceId, String filePath) async {
    final db = await AppDatabase.instance;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    await db.update(
      'cached_resources',
      {
        'local_file_path': filePath,
        'updated_at': now,
      },
      where: 'resource_id = ?',
      whereArgs: [resourceId],
    );
  }

  Future<void> _trimDocuments(Database db) async {
    final rows = await db.rawQuery('''
      SELECT scope_key
      FROM cached_documents
      GROUP BY scope_key
      ORDER BY MAX(updated_at) DESC
      LIMIT -1 OFFSET 8
    ''');
    if (rows.isEmpty) return;
    final scopeKeys =
        rows.map((row) => row['scope_key']).whereType<String>().toList();
    final placeholders = List.filled(scopeKeys.length, '?').join(', ');
    await db.delete(
      'cached_documents',
      where: 'scope_key IN ($placeholders)',
      whereArgs: scopeKeys,
    );
  }

  Future<void> _trimResources(Database db) async {
    final rows = await db.rawQuery('''
      SELECT scope_key
      FROM cached_resources
      GROUP BY scope_key
      ORDER BY MAX(updated_at) DESC
      LIMIT -1 OFFSET 8
    ''');
    if (rows.isEmpty) return;
    final scopeKeys =
        rows.map((row) => row['scope_key']).whereType<String>().toList();
    final placeholders = List.filled(scopeKeys.length, '?').join(', ');
    await db.delete(
      'cached_resources',
      where: 'scope_key IN ($placeholders)',
      whereArgs: scopeKeys,
    );
  }
}
