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

class ConnectivityService {
  final Connectivity _connectivity = Connectivity();
  final ApiClient _api;
  final OfflineQueue _queue;
  final CacheStore _cache;
  StreamSubscription<List<ConnectivityResult>>? _subscription;
  bool _isOnline = true;

  bool get isOnline => _isOnline;

  ConnectivityService({
    required ApiClient api,
    required OfflineQueue queue,
    required CacheStore cache,
  })  : _api = api,
        _queue = queue,
        _cache = cache;

  /// Start monitoring connectivity.
  Future<void> initialize() async {
    final results = await _connectivity.checkConnectivity();
    _isOnline = !results.contains(ConnectivityResult.none);

    _subscription = _connectivity.onConnectivityChanged.listen((results) {
      final wasOffline = !_isOnline;
      _isOnline = !results.contains(ConnectivityResult.none);

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
    final pending = await _queue.getPending();
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
  }

  /// Dispose connectivity listener.
  void dispose() {
    _subscription?.cancel();
  }
}
