import 'package:connectivity_plus_platform_interface/connectivity_plus_platform_interface.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/domain/entities/sync.dart';

import 'helpers/fake_app_environment.dart';
import 'helpers/integration_app.dart';
import '../test/helpers/api_responses.dart';
import '../test/helpers/test_mocks.dart';
import '../test/helpers/test_services.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late ConnectivityPlatform originalPlatform;

  setUpAll(registerTestFallbacks);

  setUp(() {
    originalPlatform = ConnectivityPlatform.instance;
  });

  tearDown(() {
    ConnectivityPlatform.instance = originalPlatform;
  });

  group('Offline sync flow', () {
    testWidgets('queues an action offline and syncs it on reconnect',
        (tester) async {
      final connectivityPlatform = TestConnectivityPlatform(
        initialResults: const [ConnectivityResult.none],
      );
      ConnectivityPlatform.instance = connectivityPlatform;

      final environment = FakeAppEnvironment();
      final api = MockApiClient();
      final syncRepository = MockSyncRepository();

      _stubApiClient(api);
      _stubSyncRepository(syncRepository);
      when(
        () => api.post(
          '/attendance/class/class-1',
          body: const {'status': 'present'},
        ),
      ).thenAnswer((_) async => response(const {'ok': true}));

      final container = await pumpIntegrationApp(
        tester,
        overrides: [
          ...environment.overrides(),
          apiClientProvider.overrideWithValue(api),
          syncRepositoryProvider.overrideWithValue(syncRepository),
        ],
      );

      await environment.offlineQueue.enqueue(
        method: 'POST',
        path: '/attendance/class/class-1',
        body: const {'status': 'present'},
      );
      await environment.cacheStore.put(
        'feed:first',
        const [
          {'id': 'feed-1'}
        ],
        60,
      );
      await environment.cacheStore.put(
        'notifications:first',
        const [
          {'id': 'notification-1'}
        ],
        60,
      );

      final service = container.read(connectivityServiceProvider);
      await service.initialize();

      connectivityPlatform.emit(const [ConnectivityResult.wifi]);
      await _flushAsync();

      verify(
        () => api.post(
          '/attendance/class/class-1',
          body: const {'status': 'present'},
        ),
      ).called(1);
      expect(await environment.offlineQueue.pendingCount(), 0);
      expect(await environment.offlineQueue.failedCount(), 0);
      expect(await environment.cacheStore.get('feed:first'), isNull);
      expect(await environment.cacheStore.get('notifications:first'), isNull);
      expect(service.indicator.online, isTrue);
      expect(service.indicator.lastSyncAt, isNotNull);

      service.dispose();
      await connectivityPlatform.disposePlatform();
    });

    testWidgets('pushes queued changes then pulls and checkpoints on reconnect',
        (tester) async {
      final connectivityPlatform = TestConnectivityPlatform(
        initialResults: const [ConnectivityResult.none],
      );
      ConnectivityPlatform.instance = connectivityPlatform;

      final environment = FakeAppEnvironment();
      final api = MockApiClient();
      final syncRepository = MockSyncRepository();

      _stubApiClient(api);
      _stubSyncRepository(syncRepository);
      when(
        () => api.post(
          '/content/items',
          body: const {'title': 'Worksheet'},
        ),
      ).thenAnswer((_) async => response(const {'id': 'content-1'}));
      when(
        () => api.put(
          '/content/items/content-1',
          body: const {'title': 'Updated worksheet'},
        ),
      ).thenAnswer((_) async => response(const {'id': 'content-1'}));

      final container = await pumpIntegrationApp(
        tester,
        overrides: [
          ...environment.overrides(),
          apiClientProvider.overrideWithValue(api),
          syncRepositoryProvider.overrideWithValue(syncRepository),
        ],
      );

      await environment.offlineQueue.enqueue(
        method: 'POST',
        path: '/content/items',
        body: const {'title': 'Worksheet'},
      );
      await environment.offlineQueue.enqueue(
        method: 'PUT',
        path: '/content/items/content-1',
        body: const {'title': 'Updated worksheet'},
      );

      final service = container.read(connectivityServiceProvider);
      await service.initialize();

      connectivityPlatform.emit(const [ConnectivityResult.mobile]);
      await _flushAsync();

      final pushedPayload = verify(
        () => syncRepository.pushChanges('mobile-primary', captureAny()),
      ).captured.single as Map<String, dynamic>;

      expect((pushedPayload['changes'] as List<dynamic>), hasLength(2));
      verifyInOrder([
        () => syncRepository.pushChanges('mobile-primary', any()),
        () => api.post(
              '/content/items',
              body: const {'title': 'Worksheet'},
            ),
        () => api.put(
              '/content/items/content-1',
              body: const {'title': 'Updated worksheet'},
            ),
        () => syncRepository.pullChanges('mobile-primary'),
        () => syncRepository.createCheckpoint('mobile-primary', any()),
      ]);
      expect(await environment.offlineQueue.pendingCount(), 0);

      service.dispose();
      await connectivityPlatform.disposePlatform();
    });

    testWidgets('retries failed commands after connectivity is restored again',
        (tester) async {
      final connectivityPlatform = TestConnectivityPlatform(
        initialResults: const [ConnectivityResult.none],
      );
      ConnectivityPlatform.instance = connectivityPlatform;

      final environment = FakeAppEnvironment();
      final api = MockApiClient();
      final syncRepository = MockSyncRepository();
      var attempts = 0;

      _stubApiClient(api);
      _stubSyncRepository(syncRepository);
      when(
        () => api.post(
          '/attendance/class/class-1',
          body: const {'status': 'late'},
        ),
      ).thenAnswer((_) async {
        if (attempts++ == 0) {
          throw const ApiClientError(
            500,
            ApiError(
              code: 'ERR-SYS-500',
              message: 'temporary outage',
              category: 'system',
              retryable: true,
            ),
          );
        }
        return response(const {'ok': true});
      });

      final container = await pumpIntegrationApp(
        tester,
        overrides: [
          ...environment.overrides(),
          apiClientProvider.overrideWithValue(api),
          syncRepositoryProvider.overrideWithValue(syncRepository),
        ],
      );

      final commandId = await environment.offlineQueue.enqueue(
        method: 'POST',
        path: '/attendance/class/class-1',
        body: const {'status': 'late'},
      );

      final service = container.read(connectivityServiceProvider);
      await service.initialize();

      connectivityPlatform.emit(const [ConnectivityResult.wifi]);
      await _flushAsync();

      expect(await environment.offlineQueue.pendingCount(), 0);
      expect(await environment.offlineQueue.failedCount(), 1);
      final failedCommand = (await environment.offlineQueue.getFailed()).single;
      expect(failedCommand.id, commandId);
      expect(failedCommand.retryCount, 1);

      await environment.offlineQueue.resetToPending(commandId);
      connectivityPlatform.emit(const [ConnectivityResult.none]);
      await _flushAsync();
      connectivityPlatform.emit(const [ConnectivityResult.mobile]);
      await _flushAsync();

      verify(
        () => api.post(
          '/attendance/class/class-1',
          body: const {'status': 'late'},
        ),
      ).called(2);
      expect(await environment.offlineQueue.pendingCount(), 0);
      expect(await environment.offlineQueue.failedCount(), 0);

      service.dispose();
      await connectivityPlatform.disposePlatform();
    });
  });
}

void _stubApiClient(MockApiClient api) {
  when(() => api.setLocale(any())).thenReturn(null);
}

void _stubSyncRepository(MockSyncRepository syncRepository) {
  when(() => syncRepository.registerDevice(any())).thenAnswer(
    (_) async => const SyncDevice(
      id: 'device-1',
      deviceName: 'Ecole mobile',
      deviceType: 'mobile',
      isActive: true,
    ),
  );
  when(() => syncRepository.pushChanges('mobile-primary', any())).thenAnswer(
    (_) async => const {'accepted': 1},
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
}

Future<void> _flushAsync() async {
  await Future<void>.delayed(const Duration(milliseconds: 20));
  await Future<void>.delayed(const Duration(milliseconds: 20));
}
