import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

import 'package:ecole_platform/data/local_store/database.dart';

const _testDbName = 'ecole_platform.db';

bool _databaseFactoryInitialized = false;

Future<void> initializeTestDatabase() async {
  TestWidgetsFlutterBinding.ensureInitialized();
  if (!_databaseFactoryInitialized) {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
    _databaseFactoryInitialized = true;
  }
  await resetTestDatabase();
}

Future<void> resetTestDatabase() async {
  await AppDatabase.close();
  final dbPath = await getDatabasesPath();
  await databaseFactory.deleteDatabase('$dbPath/$_testDbName');
}
