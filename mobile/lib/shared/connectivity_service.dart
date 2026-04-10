/// Connectivity service — monitors network state, replays offline queue.
///
/// Reference: DEC-E2-023 — Replay on reconnection
/// Watches connectivity changes and replays pending write commands.

import 'dart:async';
import 'dart:developer' as dev;

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:ecole_platform/data/api/api_client.dart';
import 'package:ecole_platform/data/local_store/cache_store.dart';
import 'package:ecole_platform/data/local_store/offline_queue.dart';
import 'package:ecole_platform/domain/entities/sync.dart';
import 'package:ecole_platform/domain/repositories/sync_repository.dart';

class ConnectivityService {
  final Connectivity _connectivity = Connectivity();
  final ApiClient _api;
  final OfflineQueue _queue;
  final CacheStore _cache;
  final SyncRepository? _syncRepository;
  StreamSubscription<List<ConnectivityResult>>? _subscription;
  bool _isOnline = true;
  bool _syncing = false;
  String? _lastSyncAt;
  final String _deviceId = 'mobile-primary';

  bool get isOnline => _isOnline;
  String get deviceId => _deviceId;
  SyncIndicatorState get indicator => SyncIndicatorState(
        online: _isOnline,
        syncing: _syncing,
        pendingCount: _pendingCount,
        failedCount: _failedCount,
        lastSyncAt: _lastSyncAt,
      );
  final StreamController<SyncIndicatorState> _indicatorController =
      StreamController<SyncIndicatorState>.broadcast();
  Stream<SyncIndicatorState> get indicatorStream => _indicatorController.stream;
  int _pendingCount = 0;
  int _failedCount = 0;

  ConnectivityService({
    required ApiClient api,
    required OfflineQueue queue,
    required CacheStore cache,
    SyncRepository? syncRepository,
  })  : _api = api,
        _queue = queue,
        _cache = cache,
        _syncRepository = syncRepository;

  /// Start monitoring connectivity.
  Future<void> initialize() async {
    final results = await _connectivity.checkConnectivity();
    _isOnline = !results.contains(ConnectivityResult.none);
    await _refreshIndicator();
    _indicatorController.add(indicator);
    await _registerDeviceIfPossible();

    _subscription = _connectivity.onConnectivityChanged.listen((results) {
      final wasOffline = !_isOnline;
      _isOnline = !results.contains(ConnectivityResult.none);
      _indicatorController.add(indicator);

      if (wasOffline && _isOnline) {
        dev.log('Back online — replaying queue', name: 'Connectivity');
        _replayQueue();
        // Invalidate short-TTL caches on reconnect
        _cache.invalidatePrefix('feed:');
        _cache.invalidatePrefix('notifications:');
      }
    });
  }

  /// Replay all pending commands in order.
  Future<void> _replayQueue() async {
    _syncing = true;
    await _refreshIndicator();
    _indicatorController.add(indicator);
    final pending = await _queue.getPending();
    if (_syncRepository != null) {
      try {
        await _syncRepository.pushChanges(_deviceId, {
          'changes': pending
              .map((cmd) => {
                    'method': cmd.method,
                    'path': cmd.path,
                    'body': cmd.bodyJson,
                  })
              .toList(),
        });
      } catch (e) {
        dev.log('Sync push failed: $e', name: 'Connectivity');
      }
    }
    for (final cmd in pending) {
      try {
        if (cmd.method == 'POST') {
          await _api.post(cmd.path, body: cmd.bodyJson);
        } else if (cmd.method == 'PUT') {
          await _api.put(cmd.path, body: cmd.bodyJson);
        }
        await _queue.markCompleted(cmd.id);
        dev.log('Replayed: ${cmd.method} ${cmd.path}', name: 'Connectivity');
      } catch (e) {
        await _queue.markFailed(cmd.id, e.toString());
        dev.log('Replay failed: ${cmd.method} ${cmd.path}: $e',
            name: 'Connectivity');
        // Stop on first failure to maintain order
        break;
      }
    }
    if (_syncRepository != null) {
      try {
        await _syncRepository.pullChanges(_deviceId);
        await _syncRepository.createCheckpoint(_deviceId, {
          'checkpoint': DateTime.now().toIso8601String(),
        });
      } catch (e) {
        dev.log('Sync pull/checkpoint failed: $e', name: 'Connectivity');
      }
    }
    _lastSyncAt = DateTime.now().toIso8601String();
    _syncing = false;
    await _refreshIndicator();
    _indicatorController.add(indicator);
  }

  Future<void> _registerDeviceIfPossible() async {
    if (_syncRepository == null) return;
    try {
      await _syncRepository.registerDevice({
        'device_id': _deviceId,
        'device_name': 'Ecole mobile',
        'device_type': 'mobile',
      });
    } catch (e) {
      dev.log('Sync device registration failed: $e', name: 'Connectivity');
    }
  }

  Future<void> _refreshIndicator() async {
    _pendingCount = await _queue.pendingCount();
    _failedCount = await _queue.failedCount();
  }

  /// Dispose connectivity listener.
  void dispose() {
    _subscription?.cancel();
    _indicatorController.close();
  }
}
