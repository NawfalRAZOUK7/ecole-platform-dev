import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/local_store/attendance_store.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/data/local_store/documents_store.dart';
import 'package:ecole_platform/data/local_store/events_store.dart';
import 'package:ecole_platform/data/local_store/notifications_store.dart';
import 'package:ecole_platform/data/local_store/reports_store.dart';

class MockApiClient extends Mock implements ApiClient {}

class MockCacheStore extends Mock implements CacheStore {}

class MockAttendanceStore extends Mock implements AttendanceStore {}

class MockDocumentsStore extends Mock implements DocumentsStore {}

class MockEventsStore extends Mock implements EventsStore {}

class MockNotificationsStore extends Mock implements NotificationsStore {}

class MockReportsStore extends Mock implements ReportsStore {}

bool _fallbacksRegistered = false;

void registerTestFallbacks() {
  if (_fallbacksRegistered) {
    return;
  }
  registerFallbackValue(<String, dynamic>{});
  registerFallbackValue(<Map<String, dynamic>>[]);
  registerFallbackValue(<String>[]);
  _fallbacksRegistered = true;
}
