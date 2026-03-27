/// SQLite database setup for offline cache and write queue.
///
/// Reference: DEC-E2-021 — SQLite for local persistence
/// Two tables: cache_entries (TTL-based read cache)
///             offline_queue  (write queue for replay)

import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

const String _dbName = 'ecole_platform.db';
const int _dbVersion = 3;

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
        await _createTables(db);
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          await db.execute('''
            CREATE TABLE IF NOT EXISTS cached_notifications (
              notification_id TEXT PRIMARY KEY,
              payload TEXT NOT NULL,
              created_at INTEGER NOT NULL,
              updated_at INTEGER NOT NULL
            )
          ''');
          await db.execute('''
            CREATE INDEX IF NOT EXISTS idx_cached_notifications_updated
            ON cached_notifications(updated_at)
          ''');
        }
        if (oldVersion < 3) {
          await db.execute('''
            CREATE TABLE IF NOT EXISTS cached_reports (
              report_job_id TEXT PRIMARY KEY,
              payload TEXT NOT NULL,
              file_path TEXT,
              created_at INTEGER NOT NULL,
              updated_at INTEGER NOT NULL
            )
          ''');
          await db.execute('''
            CREATE INDEX IF NOT EXISTS idx_cached_reports_updated
            ON cached_reports(updated_at)
          ''');
        }
      },
    );
  }

  static Future<void> _createTables(Database db) async {
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

    // Structured notifications cache for the last 100 entries.
    await db.execute('''
      CREATE TABLE cached_notifications (
        notification_id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
      )
    ''');

    await db.execute('''
      CREATE INDEX idx_cache_created ON cache_entries(created_at)
    ''');

    await db.execute('''
      CREATE INDEX idx_queue_status ON offline_queue(status)
    ''');

    await db.execute('''
      CREATE INDEX idx_cached_notifications_updated
      ON cached_notifications(updated_at)
    ''');

    await db.execute('''
      CREATE TABLE cached_reports (
        report_job_id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        file_path TEXT,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
      )
    ''');

    await db.execute('''
      CREATE INDEX idx_cached_reports_updated
      ON cached_reports(updated_at)
    ''');
  }

  /// Close the database (for testing).
  static Future<void> close() async {
    await _database?.close();
    _database = null;
  }
}
