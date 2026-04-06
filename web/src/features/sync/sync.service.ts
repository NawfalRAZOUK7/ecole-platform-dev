import { api } from '@/services/api/client';
import type {
  CreateSyncCheckpointPayload,
  RegisterSyncDevicePayload,
  ResolveSyncConflictPayload,
  SyncCheckpoint,
  SyncConflict,
  SyncDevice,
  SyncHealth,
  SyncPullResponse,
  SyncPushPayload,
  SyncPushResponse,
  SyncStatus,
} from './sync.types';

export const syncService = {
  registerDevice(payload: RegisterSyncDevicePayload) {
    return api.post<SyncDevice>('/sync/devices', payload);
  },

  listDevices(params: { is_active?: boolean; device_type?: string } = {}) {
    return api.list<SyncDevice>('/sync/devices', {
      is_active: params.is_active === undefined ? undefined : String(params.is_active),
      device_type: params.device_type,
    });
  },

  pushChanges(deviceId: string, payload: SyncPushPayload) {
    return api.post<SyncPushResponse>(`/sync/push?device_id=${encodeURIComponent(deviceId)}`, payload);
  },

  pullChanges(deviceId: string, sinceCheckpoint?: string, limit = 100) {
    return api.post<SyncPullResponse>(
      `/sync/pull?device_id=${encodeURIComponent(deviceId)}&limit=${limit}${sinceCheckpoint ? `&since_checkpoint=${encodeURIComponent(sinceCheckpoint)}` : ''}`
    );
  },

  getStatus(deviceId: string) {
    return api.get<SyncStatus>('/sync/status', {
      device_id: deviceId,
    });
  },

  listConflicts(resolution = 'pending', limit = 100) {
    return api.list<SyncConflict>('/sync/conflicts', {
      resolution,
      limit,
    });
  },

  resolveConflict(conflictId: string, payload: ResolveSyncConflictPayload) {
    return api.post<SyncConflict>(`/sync/conflicts/${conflictId}/resolve`, payload);
  },

  listCheckpoints(deviceId?: string, limit = 100) {
    return api.list<SyncCheckpoint>('/sync/checkpoints', {
      device_id: deviceId,
      limit,
    });
  },

  createCheckpoint(deviceId: string, payload: CreateSyncCheckpointPayload) {
    return api.post<SyncCheckpoint>(`/sync/checkpoint?device_id=${encodeURIComponent(deviceId)}`, payload);
  },

  getHealth(deviceId: string) {
    return api.get<SyncHealth>('/sync/health', {
      device_id: deviceId,
    });
  },
};
