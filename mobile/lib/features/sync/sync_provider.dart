import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:ecole_platform/app/providers.dart';
import 'package:ecole_platform/domain/entities/sync.dart';

final syncStatusProvider = FutureProvider<SyncStatusBundle>((ref) async {
  final service = ref.read(connectivityServiceProvider);
  final deviceId = service.deviceId;
  final repository = ref.read(syncRepositoryProvider);
  final results = await Future.wait<dynamic>([
    repository.getStatus(deviceId),
    repository.getHealth(deviceId),
    repository.listDevices(),
    repository.listCheckpoints(deviceId: deviceId),
  ]);
  return SyncStatusBundle(
    status: results[0] as SyncStatus,
    health: results[1] as SyncHealth,
    devices: results[2] as List<SyncDevice>,
    checkpoints: results[3] as List<SyncCheckpoint>,
    indicator: service.indicator,
  );
});

final syncConflictsProvider = FutureProvider<List<SyncConflict>>((ref) async {
  return ref.read(syncRepositoryProvider).listConflicts();
});
