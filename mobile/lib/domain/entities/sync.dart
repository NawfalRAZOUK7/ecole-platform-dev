class SyncDevice {
  final String id;
  final String deviceName;
  final String deviceType;
  final bool isActive;

  const SyncDevice({
    required this.id,
    required this.deviceName,
    required this.deviceType,
    required this.isActive,
  });

  factory SyncDevice.fromJson(Map<String, dynamic> json) {
    return SyncDevice(
      id: json['id']?.toString() ?? '',
      deviceName: json['device_name']?.toString() ?? json['name']?.toString() ?? '',
      deviceType: json['device_type']?.toString() ?? 'mobile',
      isActive: json['is_active'] as bool? ?? true,
    );
  }
}

class SyncStatus {
  final int pendingOperations;
  final String? lastSyncAt;
  final String? lastCheckpoint;
  final bool online;

  const SyncStatus({
    required this.pendingOperations,
    required this.online,
    this.lastSyncAt,
    this.lastCheckpoint,
  });

  factory SyncStatus.fromJson(Map<String, dynamic> json) {
    return SyncStatus(
      pendingOperations: (json['pending_operations'] as num?)?.toInt() ??
          (json['pending_count'] as num?)?.toInt() ??
          0,
      lastSyncAt: json['last_sync_at']?.toString(),
      lastCheckpoint: json['last_checkpoint']?.toString(),
      online: json['online'] as bool? ?? true,
    );
  }
}

class SyncConflict {
  final String id;
  final String entityType;
  final String entityId;
  final String resolution;
  final String summary;

  const SyncConflict({
    required this.id,
    required this.entityType,
    required this.entityId,
    required this.resolution,
    required this.summary,
  });

  factory SyncConflict.fromJson(Map<String, dynamic> json) {
    return SyncConflict(
      id: json['id']?.toString() ?? '',
      entityType: json['entity_type']?.toString() ?? '',
      entityId: json['entity_id']?.toString() ?? '',
      resolution: json['resolution']?.toString() ?? 'pending',
      summary: json['summary']?.toString() ??
          json['message']?.toString() ??
          '${json['entity_type']}:${json['entity_id']}',
    );
  }
}

class SyncCheckpoint {
  final String id;
  final String? checkpoint;

  const SyncCheckpoint({
    required this.id,
    this.checkpoint,
  });

  factory SyncCheckpoint.fromJson(Map<String, dynamic> json) {
    return SyncCheckpoint(
      id: json['id']?.toString() ?? '',
      checkpoint: json['checkpoint']?.toString(),
    );
  }
}

class SyncHealth {
  final bool healthy;
  final int queueDepth;
  final double latencyMs;

  const SyncHealth({
    required this.healthy,
    required this.queueDepth,
    required this.latencyMs,
  });

  factory SyncHealth.fromJson(Map<String, dynamic> json) {
    return SyncHealth(
      healthy: json['healthy'] as bool? ?? true,
      queueDepth: (json['queue_depth'] as num?)?.toInt() ?? 0,
      latencyMs: (json['latency_ms'] as num?)?.toDouble() ?? 0,
    );
  }
}

class SyncIndicatorState {
  final bool online;
  final bool syncing;
  final int pendingCount;
  final int failedCount;
  final String? lastSyncAt;

  const SyncIndicatorState({
    required this.online,
    required this.syncing,
    required this.pendingCount,
    required this.failedCount,
    this.lastSyncAt,
  });
}

class SyncStatusBundle {
  final SyncStatus status;
  final SyncHealth health;
  final List<SyncDevice> devices;
  final List<SyncCheckpoint> checkpoints;
  final SyncIndicatorState indicator;

  const SyncStatusBundle({
    required this.status,
    required this.health,
    required this.devices,
    required this.checkpoints,
    required this.indicator,
  });
}
