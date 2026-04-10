import 'package:ecole_platform/domain/entities/sync.dart';

abstract class SyncRepository {
  Future<SyncDevice> registerDevice(Map<String, dynamic> payload);

  Future<List<SyncDevice>> listDevices({Map<String, dynamic>? params});

  Future<Map<String, dynamic>> pushChanges(
    String deviceId,
    Map<String, dynamic> payload,
  );

  Future<Map<String, dynamic>> pullChanges(
    String deviceId, {
    String? sinceCheckpoint,
    int limit = 100,
  });

  Future<SyncStatus> getStatus(String deviceId);

  Future<List<SyncConflict>> listConflicts({
    String resolution = 'pending',
    int limit = 100,
  });

  Future<SyncConflict> resolveConflict(
    String conflictId,
    Map<String, dynamic> payload,
  );

  Future<List<SyncCheckpoint>> listCheckpoints({
    String? deviceId,
    int limit = 100,
  });

  Future<SyncCheckpoint> createCheckpoint(
    String deviceId,
    Map<String, dynamic> payload,
  );

  Future<SyncHealth> getHealth(String deviceId);
}
