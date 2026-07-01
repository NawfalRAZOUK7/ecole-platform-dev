export interface SyncDevice {
  id: string;
  school_id: string;
  device_name: string;
  device_type: string;
  last_seen_at: string;
  firmware_version?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface RegisterSyncDevicePayload {
  device_name: string;
  device_type: 'local_server' | 'mobile' | 'browser';
  firmware_version?: string | null;
}

export interface SyncQueueItem {
  id: string;
  school_id: string;
  device_id: string;
  entity_type: string;
  entity_id: string;
  operation: string;
  payload: Record<string, unknown>;
  status: string;
  retry_count: number;
  synced_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface SyncPushPayload {
  items: Array<{
    entity_type: string;
    entity_id: string;
    operation: 'create' | 'update' | 'delete';
    payload: Record<string, unknown>;
    created_at?: string;
  }>;
}

export interface SyncPushResponse {
  device_id: string;
  accepted_count: number;
  conflict_count: number;
  queued_items: SyncQueueItem[];
  conflict_ids: string[];
}

export interface SyncPullResponse {
  device_id: string;
  since_checkpoint?: string | null;
  changes: SyncQueueItem[];
  next_checkpoint_id?: string | null;
  conflict_count: number;
}

export interface SyncStatus {
  device_id: string;
  pending_count: number;
  synced_count: number;
  conflict_count: number;
  failed_count: number;
  last_checkpoint_id?: string | null;
  last_sync_at?: string | null;
}

export interface SyncConflict {
  id: string;
  school_id: string;
  queue_item_id: string;
  entity_type: string;
  entity_id: string;
  client_payload: Record<string, unknown>;
  server_payload: Record<string, unknown>;
  resolution: 'pending' | 'client_wins' | 'server_wins' | 'manual';
  resolved_by?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface ResolveSyncConflictPayload {
  resolution: 'pending' | 'client_wins' | 'server_wins' | 'manual';
}

export interface SyncCheckpoint {
  id: string;
  school_id: string;
  device_id: string;
  last_sync_at: string;
  last_entity_type: string;
  last_entity_id: string;
  records_synced: number;
  created_at: string;
  updated_at?: string | null;
}

export interface CreateSyncCheckpointPayload {
  last_entity_type: string;
  last_entity_id: string;
  records_synced: number;
}

export interface SyncHealth {
  device_id: string;
  health: string;
  is_active: boolean;
  pending_count: number;
  conflict_count: number;
  failed_count: number;
  last_seen_at: string;
  last_sync_at?: string | null;
}
