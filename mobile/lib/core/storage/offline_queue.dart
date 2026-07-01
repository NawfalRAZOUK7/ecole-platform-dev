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

enum SyncEndpoint {
  attendanceClass,
  attendanceHistory,
  contentItem,
  contentLibrary,
  gradebookGrade,
  invoicePaymentProof,
  budgetRequest,
  microSchoolEnrollment,
  questionBankImport,
  quizAttempt,
  timetableGeneration,
}

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

  SyncEndpoint? get syncEndpoint => OfflineQueue.resolveSyncEndpoint(path);
}

class OfflineQueue {
  static final List<MapEntry<Pattern, SyncEndpoint>> _syncEndpointMatchers = [
    MapEntry(RegExp(r'^/attendance/class/'), SyncEndpoint.attendanceClass),
    MapEntry(RegExp(r'^/attendance/history'), SyncEndpoint.attendanceHistory),
    MapEntry(RegExp(r'^/content/items'), SyncEndpoint.contentItem),
    MapEntry(RegExp(r'^/teacher/content-library'), SyncEndpoint.contentLibrary),
    MapEntry(RegExp(r'^/gradebook/grades'), SyncEndpoint.gradebookGrade),
    MapEntry(
      RegExp(r'^/invoices/.*/payment-proof'),
      SyncEndpoint.invoicePaymentProof,
    ),
    MapEntry(RegExp(r'^/budgets/requests'), SyncEndpoint.budgetRequest),
    MapEntry(
      RegExp(r'^/micro-schools/.*/enroll'),
      SyncEndpoint.microSchoolEnrollment,
    ),
    MapEntry(
      RegExp(r'^/question-bank/import'),
      SyncEndpoint.questionBankImport,
    ),
    MapEntry(RegExp(r'^/quiz/attempts'), SyncEndpoint.quizAttempt),
    MapEntry(
      RegExp(r'^/timetable/generation'),
      SyncEndpoint.timetableGeneration,
    ),
  ];

  static SyncEndpoint? resolveSyncEndpoint(String path) {
    for (final matcher in _syncEndpointMatchers) {
      final pattern = matcher.key;
      if (pattern is RegExp && pattern.hasMatch(path)) {
        return matcher.value;
      }
      if (pattern is String && path.contains(pattern)) {
        return matcher.value;
      }
    }
    return null;
  }

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

  Future<List<QueuedCommand>> getFailed() async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'offline_queue',
      where: 'status = ?',
      whereArgs: ['failed_command'],
      orderBy: 'created_at DESC',
    );
    return rows.map(QueuedCommand.fromRow).toList();
  }

  Future<List<QueuedCommand>> getAll() async {
    final db = await AppDatabase.instance;
    final rows = await db.query('offline_queue', orderBy: 'created_at DESC');
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

  Future<int> failedCount() async {
    final db = await AppDatabase.instance;
    final result = await db.rawQuery(
      'SELECT COUNT(*) as count FROM offline_queue WHERE status = ?',
      ['failed_command'],
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
