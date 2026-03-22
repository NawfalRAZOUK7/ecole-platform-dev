/// Quiz offline store — persistent cache for quiz questions and draft answers.
///
/// Phase 10C: Enables offline quiz attempts.
/// - Caches quiz questions in SQLite for offline access
/// - Stores draft answers locally, syncs when online
/// - Integrates with existing OfflineQueue for answer submission

import 'dart:convert';
import 'database.dart';

class QuizOfflineStore {
  /// Store quiz questions for offline use.
  Future<void> cacheQuizQuestions(
      String quizId, List<Map<String, dynamic>> questions) async {
    final db = await AppDatabase.instance;

    // Use cache_entries table with long TTL
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    await db.insert(
      'cache_entries',
      {
        'cache_key': 'quiz_questions:$quizId',
        'data': jsonEncode(questions),
        'created_at': now,
        'ttl_seconds': 7 * 24 * 3600, // 7 days
      },
      conflictAlgorithm: 1, // replace
    );
  }

  /// Get cached quiz questions.
  Future<List<Map<String, dynamic>>?> getCachedQuestions(String quizId) async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cache_entries',
      where: 'cache_key = ?',
      whereArgs: ['quiz_questions:$quizId'],
    );

    if (rows.isEmpty) return null;

    final entry = rows.first;
    final createdAt = entry['created_at'] as int;
    final ttlSeconds = entry['ttl_seconds'] as int;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;

    if (now - createdAt > ttlSeconds) return null;

    final data = jsonDecode(entry['data'] as String) as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  /// Store draft answers locally (for offline resumption).
  Future<void> saveDraftAnswers(
      String attemptId, Map<String, dynamic> answers) async {
    final db = await AppDatabase.instance;
    final now = DateTime.now().millisecondsSinceEpoch ~/ 1000;
    await db.insert(
      'cache_entries',
      {
        'cache_key': 'quiz_draft:$attemptId',
        'data': jsonEncode([answers]),
        'created_at': now,
        'ttl_seconds': 24 * 3600, // 24 hours
      },
      conflictAlgorithm: 1,
    );
  }

  /// Get draft answers for an attempt.
  Future<Map<String, dynamic>?> getDraftAnswers(String attemptId) async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cache_entries',
      where: 'cache_key = ?',
      whereArgs: ['quiz_draft:$attemptId'],
    );

    if (rows.isEmpty) return null;

    final data = jsonDecode(rows.first['data'] as String) as List<dynamic>;
    if (data.isEmpty) return null;
    return data.first as Map<String, dynamic>;
  }

  /// Clear draft answers after successful submission.
  Future<void> clearDraft(String attemptId) async {
    final db = await AppDatabase.instance;
    await db.delete(
      'cache_entries',
      where: 'cache_key = ?',
      whereArgs: ['quiz_draft:$attemptId'],
    );
  }

  /// List all cached quiz IDs (for "available offline" indicator).
  Future<List<String>> getCachedQuizIds() async {
    final db = await AppDatabase.instance;
    final rows = await db.query(
      'cache_entries',
      columns: ['cache_key'],
      where: 'cache_key LIKE ?',
      whereArgs: ['quiz_questions:%'],
    );

    return rows
        .map((r) => (r['cache_key'] as String).replaceFirst('quiz_questions:', ''))
        .toList();
  }
}
