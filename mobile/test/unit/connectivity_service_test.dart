import 'package:connectivity_plus_platform_interface/connectivity_plus_platform_interface.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/core/storage/cache_store.dart';
import 'package:ecole_platform/core/storage/offline_queue.dart';
import 'package:ecole_platform/domain/entities/sync/sync.dart';
import 'package:ecole_platform/core/network/connectivity.dart';

import '../helpers/api_responses.dart';
import '../helpers/test_database.dart';
import '../helpers/test_mocks.dart';
import '../helpers/test_services.dart';

void main() {
  late ConnectivityPlatform originalPlatform;

  setUpAll(() async {
    await initializeTestDatabase();
    registerTestFallbacks();
  });

  setUp(() async {
    originalPlatform = ConnectivityPlatform.instance;
    await resetTestDatabase();
  });

  tearDown(() {
    ConnectivityPlatform.instance = originalPlatform;
  });

  test('detects offline state and updates when connectivity returns', () async {
    final connectivityPlatform = TestConnectivityPlatform(
      initialResults: const [ConnectivityResult.none],
    );
    ConnectivityPlatform.instance = connectivityPlatform;

    final service = ConnectivityService(
      api: MockApiClient(),
      queue: OfflineQueue(),
      cache: CacheStore(),
    );

    await service.initialize();
    expect(service.isOnline, isFalse);
    expect(service.indicator.online, isFalse);

    connectivityPlatform.emit(const [ConnectivityResult.wifi]);
    await _flushAsync();

    expect(service.isOnline, isTrue);
    expect(service.indicator.online, isTrue);

    service.dispose();
    await connectivityPlatform.disposePlatform();
  });

  test('replays queued commands and invalidates short-lived cache on reconnect',
      () async {
    final connectivityPlatform = TestConnectivityPlatform(
      initialResults: const [ConnectivityResult.none],
    );
    ConnectivityPlatform.instance = connectivityPlatform;

    final api = MockApiClient();
    final queue = OfflineQueue();
    final cache = CacheStore();

    await queue.enqueue(
      method: 'POST',
      path: '/attendance/class/class-1',
      body: const {'status': 'present'},
    );
    await cache.put(
      'feed:first',
      const [
        {'id': 'feed-1'},
      ],
      CacheTtl.feed,
    );
    await cache.put(
      'notifications:first',
      const [
        {'id': 'notification-1'},
      ],
      CacheTtl.notifications,
    );

    when(
      () => api.post(
        '/attendance/class/class-1',
        body: const {'status': 'present'},
      ),
    ).thenAnswer((_) async => response(const {'ok': true}));

    final service = ConnectivityService(api: api, queue: queue, cache: cache);

    await service.initialize();
    connectivityPlatform.emit(const [ConnectivityResult.mobile]);
    await untilCalled(
      () => api.post(
        '/attendance/class/class-1',
        body: const {'status': 'present'},
      ),
    );
    await _flushAsync();

    verify(
      () => api.post(
        '/attendance/class/class-1',
        body: const {'status': 'present'},
      ),
    ).called(1);
    expect(await queue.pendingCount(), 0);
    expect(await cache.get('feed:first'), isNull);
    expect(await cache.get('notifications:first'), isNull);

    service.dispose();
    await connectivityPlatform.disposePlatform();
  });

  test('pushes queued changes then pulls and checkpoints on reconnect',
      () async {
    final connectivityPlatform = TestConnectivityPlatform(
      initialResults: const [ConnectivityResult.none],
    );
    ConnectivityPlatform.instance = connectivityPlatform;

    final api = MockApiClient();
    final syncRepository = MockSyncRepository();
    final queue = OfflineQueue();

    await queue.enqueue(
      method: 'POST',
      path: '/content/items',
      body: const {'title': 'Worksheet'},
    );
    await queue.enqueue(
      method: 'PUT',
      path: '/content/items/content-1',
      body: const {'title': 'Updated worksheet'},
    );

    when(() => syncRepository.registerDevice(any())).thenAnswer(
      (_) async => const SyncDevice(
        id: 'device-1',
        deviceName: 'Ecole mobile',
        deviceType: 'mobile',
        isActive: true,
      ),
    );
    when(() => syncRepository.pushChanges('mobile-primary', any())).thenAnswer(
      (_) async => const {'accepted': 2},
    );
    when(() => syncRepository.pullChanges('mobile-primary')).thenAnswer(
      (_) async => const {'changes': []},
    );
    when(
      () => syncRepository.createCheckpoint('mobile-primary', any()),
    ).thenAnswer(
      (_) async => const SyncCheckpoint(
        id: 'checkpoint-1',
        checkpoint: '2026-04-12T10:00:00Z',
      ),
    );
    when(
      () => api.post('/content/items', body: const {'title': 'Worksheet'}),
    ).thenAnswer((_) async => response(const {'id': 'content-1'}));
    when(
      () => api.put(
        '/content/items/content-1',
        body: const {'title': 'Updated worksheet'},
      ),
    ).thenAnswer((_) async => response(const {'id': 'content-1'}));

    final service = ConnectivityService(
      api: api,
      queue: queue,
      cache: CacheStore(),
      syncRepository: syncRepository,
    );

    await service.initialize();
    connectivityPlatform.emit(const [ConnectivityResult.wifi]);
    await untilCalled(
      () => syncRepository.pushChanges('mobile-primary', any()),
    );
    await _flushAsync();

    final capturedPayload = verify(
      () => syncRepository.pushChanges('mobile-primary', captureAny()),
    ).captured.single as Map<String, dynamic>;

    expect((capturedPayload['changes'] as List<dynamic>), hasLength(2));
    verify(() => syncRepository.pullChanges('mobile-primary')).called(1);
    verify(
      () => syncRepository.createCheckpoint('mobile-primary', any()),
    ).called(1);
    expect(service.indicator.lastSyncAt, isNotNull);

    service.dispose();
    await connectivityPlatform.disposePlatform();
  });
}

Future<void> _flushAsync() async {
  await Future<void>.delayed(const Duration(milliseconds: 20));
  await Future<void>.delayed(const Duration(milliseconds: 20));
}
