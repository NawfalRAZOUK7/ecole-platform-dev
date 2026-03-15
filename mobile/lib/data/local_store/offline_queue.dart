/// Offline write queue with SQLite persistence and replay on reconnect.
///
/// Reference: DEC-E2-023 — Server-authoritative conflict resolution
/// - Commands queued when offline
/// - Replayed in order on reconnect
/// - Failed commands tracked with status = 'failed_command'
/// - Idempotency keys prevent duplicate execution

import 'dart:convert';
import 'package:uuid/uuid.dart';

import 'database.dart';

const _uuid = Uuid();

/// A queued write command.
class QueuedCommand {
  final int id;
  final String method;
  final String path;
  final String? body;
  final String? idempotencyKey;
  final int createdAt;
  final String status;
  final int retryCount;
  final String? lastError;

  const QueuedCommand({
    required this.id,
    required this.method,
    required this.path,
    this.body,
    this.idempotencyKey,
    required this.createdAt,
    required this.status,
    required this.retryCount,
    this.lastError,
  });

  factory QueuedCommand.fromRow(Map<String, dynamic> row) {
    return QueuedCommand(
      id: row['id'] as int,
      method: row['method'] as String,
      path: row['path'] as String,
      body: row['body'] as String?,
      idempotencyKey: row['idempotency_key'] as String?,
      createdAt: row['created_at'] as int,
      status: row['status'] as String,
      retryCount: row['retry_count'] as int,
      lastError: row['last_error'] as String?,
    );
  }

  /// Parse body JSON.
  Map<String, dynamic>? get bodyJson {
    if (body == null) return null;
    return jsonDecode(body!) as Map<String, dynamic>;
  }
}

class OfflineQueue {
  /// Enqueue a write command for later replay.
  Future<int> enqueue({
    required String method,
    required String path,
    Map<String, dynamic>? body,
    String? idempotencyKey,
  }) async {
    final db = await AppDatabase.instance;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;

    return db.insert('offline_queue', {
      'method': method,
      'path': path,
      'body': body != null ? jsonEncode(body) : null,
      'idempotency_key': idempotencyKey ?? _uuid.v4(),
      'created_at': now,
      'status': 'pending',
      'retry_count': 0,
    });
  }

  /// Get all pending commands in order.
  Future<List<QueuedCommand>> getPending() async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'offline_queue',
      where: 'status = ?',
      whereArgs: ['pending'],
      orderBy: 'created_at ASC',
    );
    return rows.map(QueuedCommand.fromRow).toList();
  }

  /// Mark a command as completed (remove from queue).
  Future<void> markCompleted(int id) async {
    final db = await AppDatabase.instance;
    await db.delete('offline_queue', where: 'id = ?', whereArgs: [id]);
  }

  /// Mark a command as failed with error info.
  Future<void> markFailed(int id, String error) async {
    final db = await AppDatabase.instance;
    await db.update(
      'offline_queue',
      {
        'status': 'failed_command',
        'last_error': error,
        'retry_count': (await _getRetryCount(id)) + 1,
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Reset a failed command to pending for retry.
  Future<void> resetToPending(int id) async {
    final db = await AppDatabase.instance;
    await db.update(
      'offline_queue',
      {'status': 'pending', 'last_error': null},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  /// Get count of pending items.
  Future<int> pendingCount() async {
    final db = await AppDatabase.instance;
    final result = await db.rawQuery(
      'SELECT COUNT(*) as count FROM offline_queue WHERE status = ?',
      ['pending'],
    );
    return result.first['count'] as int;
  }

  /// Clear all queue entries.
  Future<void> clearAll() async {
    final db = await AppDatabase.instance;
    await db.delete('offline_queue');
  }

  Future<int> _getRetryCount(int id) async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'offline_queue',
      columns: ['retry_count'],
      where: 'id = ?',
      whereArgs: [id],
    );
    return rows.isEmpty ? 0 : rows.first['retry_count'] as int;
  }
}
