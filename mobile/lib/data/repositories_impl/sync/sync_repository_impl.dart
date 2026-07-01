import 'package:ecole_platform/core/network/api_client.dart';
import 'package:ecole_platform/domain/entities/sync/sync.dart';
import 'package:ecole_platform/domain/repositories/sync/sync_repository.dart';

class SyncRepositoryImpl implements SyncRepository {
  final ApiClient _api;

  SyncRepositoryImpl({required ApiClient api}) : _api = api;

  @override
  Future<SyncDevice> registerDevice(Map<String, dynamic> payload) async {
    final response = await _api.post('/sync/devices', body: payload);
    return SyncDevice.fromJson(response.data);
  }

  @override
  Future<List<SyncDevice>> listDevices({Map<String, dynamic>? params}) async {
    final response = await _api.list('/sync/devices', params: params);
    return response.data.map(SyncDevice.fromJson).toList();
  }

  @override
  Future<Map<String, dynamic>> pushChanges(
    String deviceId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post(
      '/sync/push?device_id=$deviceId',
      body: payload,
    );
    return response.data;
  }

  @override
  Future<Map<String, dynamic>> pullChanges(
    String deviceId, {
    String? sinceCheckpoint,
    int limit = 100,
  }) async {
    final suffix =
        sinceCheckpoint == null ? '' : '&since_checkpoint=$sinceCheckpoint';
    final response = await _api.post(
      '/sync/pull?device_id=$deviceId&limit=$limit$suffix',
    );
    return response.data;
  }

  @override
  Future<SyncStatus> getStatus(String deviceId) async {
    final response = await _api.get(
      '/sync/status',
      params: {'device_id': deviceId},
    );
    return SyncStatus.fromJson(response.data);
  }

  @override
  Future<List<SyncConflict>> listConflicts({
    String resolution = 'pending',
    int limit = 100,
  }) async {
    final response = await _api.list(
      '/sync/conflicts',
      params: {
        'resolution': resolution,
        'limit': limit,
      },
    );
    return response.data.map(SyncConflict.fromJson).toList();
  }

  @override
  Future<SyncConflict> resolveConflict(
    String conflictId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post(
      '/sync/conflicts/$conflictId/resolve',
      body: payload,
    );
    return SyncConflict.fromJson(response.data);
  }

  @override
  Future<List<SyncCheckpoint>> listCheckpoints({
    String? deviceId,
    int limit = 100,
  }) async {
    final response = await _api.list(
      '/sync/checkpoints',
      params: {
        if (deviceId != null) 'device_id': deviceId,
        'limit': limit,
      },
    );
    return response.data.map(SyncCheckpoint.fromJson).toList();
  }

  @override
  Future<SyncCheckpoint> createCheckpoint(
    String deviceId,
    Map<String, dynamic> payload,
  ) async {
    final response = await _api.post(
      '/sync/checkpoint?device_id=$deviceId',
      body: payload,
    );
    return SyncCheckpoint.fromJson(response.data);
  }

  @override
  Future<SyncHealth> getHealth(String deviceId) async {
    final response = await _api.get(
      '/sync/health',
      params: {'device_id': deviceId},
    );
    return SyncHealth.fromJson(response.data);
  }
}
