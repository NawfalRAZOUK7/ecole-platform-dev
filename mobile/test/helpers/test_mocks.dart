import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/core/storage/attendance_store.dart';
import 'package:ecole_platform/core/storage/cache_store.dart';
import 'package:ecole_platform/core/storage/documents_store.dart';
import 'package:ecole_platform/core/storage/events_store.dart';
import 'package:ecole_platform/core/storage/notifications_store.dart';
import 'package:ecole_platform/core/storage/reports_store.dart';
import 'package:ecole_platform/domain/entities/academic/gradebook.dart';
import 'package:ecole_platform/domain/repositories/sync/sync_repository.dart';
import 'package:ecole_platform/features/auth/biometric_service.dart';
import 'package:ecole_platform/core/storage/secure_storage.dart';

class MockApiClient extends Mock implements ApiClient {}

class MockCacheStore extends Mock implements CacheStore {}

class MockAttendanceStore extends Mock implements AttendanceStore {}

class MockDocumentsStore extends Mock implements DocumentsStore {}

class MockEventsStore extends Mock implements EventsStore {}

class MockNotificationsStore extends Mock implements NotificationsStore {}

class MockReportsStore extends Mock implements ReportsStore {}

class MockSyncRepository extends Mock implements SyncRepository {}

class MockSecureTokenStorage extends Mock implements SecureTokenStorage {}

class MockBiometricService extends Mock implements BiometricService {}

bool _fallbacksRegistered = false;

void registerTestFallbacks() {
  if (_fallbacksRegistered) {
    return;
  }
  registerFallbackValue(<String, dynamic>{});
  registerFallbackValue(<Map<String, dynamic>>[]);
  registerFallbackValue(<String>[]);
  registerFallbackValue(<dynamic>[]);
  registerFallbackValue(
    const BulkGradeUpdate(
      classId: 'class-1',
      grades: [
        GradeValueUpdate(
          studentId: 'student-1',
          assessmentId: 'assessment-1',
          value: 15.0,
        ),
      ],
    ),
  );
  _fallbacksRegistered = true;
}
