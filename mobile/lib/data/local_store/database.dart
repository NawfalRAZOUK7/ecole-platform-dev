/// SQLite database setup for offline cache and write queue.
///
/// Reference: DEC-E2-021 — SQLite for local persistence
/// Two tables: cache_entries (TTL-based read cache)
///             offline_queue  (write queue for replay)

import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

const String _dbName = 'ecole_platform.db';
const int _dbVersion = 1;

class AppDatabase {
  static Database? _database;

  /// Get or create the database singleton.
  static Future<Database> get instance async {
    if (_database != null) return _database!;
    _database = await _openDatabase();
    return _database!;
  }

  static Future<Database> _openDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, _dbName);

    return openDatabase(
      path,
      version: _dbVersion,
      onCreate: (db, version) async {
        // Cache entries table — TTL-based read cache
        await db.execute('''
          CREATE TABLE cache_entries (
            cache_key TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            ttl_seconds INTEGER NOT NULL
          )
        ''');

        // Offline write queue — commands to replay on reconnect
        await db.execute('''
          CREATE TABLE offline_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            body TEXT,
            idempotency_key TEXT,
            created_at INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            last_error TEXT
          )
        ''');

        // Index for cache cleanup
        await db.execute('''
          CREATE INDEX idx_cache_created ON cache_entries(created_at)
        ''');

        // Index for pending queue items
        await db.execute('''
          CREATE INDEX idx_queue_status ON offline_queue(status)
        ''');
      },
    );
  }

  /// Close the database (for testing).
  static Future<void> close() async {
    await _database?.close();
    _database = null;
  }
}
