import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_CONTENT } from '@/shared/hooks/useQueryDefaults';
import { syncService } from '../api/sync.api';
import type {
  CreateSyncCheckpointPayload,
  RegisterSyncDevicePayload,
  ResolveSyncConflictPayload,
  SyncPushPayload,
} from './sync.types';

export const syncQueryKeys = {
  all: ['sync'] as const,
  devices: () => [...syncQueryKeys.all, 'devices'] as const,
  status: (deviceId: string) => [...syncQueryKeys.all, 'status', deviceId] as const,
  conflicts: (resolution: string) => [...syncQueryKeys.all, 'conflicts', resolution] as const,
  checkpoints: (deviceId?: string) =>
    [...syncQueryKeys.all, 'checkpoints', deviceId || 'all'] as const,
  health: (deviceId: string) => [...syncQueryKeys.all, 'health', deviceId] as const,
};

export function useSyncDevices(enabled = true) {
  return useQuery({
    queryKey: syncQueryKeys.devices(),
    queryFn: async () => (await syncService.listDevices()).data,
    enabled,
    staleTime: STALE_CONTENT,
  });
}

export function useSyncStatus(deviceId: string, enabled = true) {
  return useQuery({
    queryKey: syncQueryKeys.status(deviceId),
    queryFn: async () => (await syncService.getStatus(deviceId)).data,
    enabled: enabled && Boolean(deviceId),
    staleTime: STALE_CONTENT,
  });
}

export function useSyncConflicts(resolution = 'pending') {
  return useQuery({
    queryKey: syncQueryKeys.conflicts(resolution),
    queryFn: async () => (await syncService.listConflicts(resolution)).data,
    staleTime: STALE_CONTENT,
  });
}

export function useSyncCheckpoints(deviceId?: string) {
  return useQuery({
    queryKey: syncQueryKeys.checkpoints(deviceId),
    queryFn: async () => (await syncService.listCheckpoints(deviceId)).data,
    staleTime: STALE_CONTENT,
  });
}

export function useSyncHealth(deviceId: string, enabled = true) {
  return useQuery({
    queryKey: syncQueryKeys.health(deviceId),
    queryFn: async () => (await syncService.getHealth(deviceId)).data,
    enabled: enabled && Boolean(deviceId),
    staleTime: STALE_CONTENT,
  });
}

export function useRegisterSyncDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: RegisterSyncDevicePayload) => syncService.registerDevice(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: syncQueryKeys.all });
    },
  });
}

export function usePushSyncChanges() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ deviceId, payload }: { deviceId: string; payload: SyncPushPayload }) =>
      syncService.pushChanges(deviceId, payload),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: syncQueryKeys.status(variables.deviceId) }),
        queryClient.invalidateQueries({ queryKey: syncQueryKeys.health(variables.deviceId) }),
      ]);
    },
  });
}

export function usePullSyncChanges() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      deviceId,
      sinceCheckpoint,
      limit,
    }: {
      deviceId: string;
      sinceCheckpoint?: string;
      limit?: number;
    }) => syncService.pullChanges(deviceId, sinceCheckpoint, limit),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: syncQueryKeys.status(variables.deviceId) }),
        queryClient.invalidateQueries({ queryKey: syncQueryKeys.health(variables.deviceId) }),
      ]);
    },
  });
}

export function useResolveSyncConflict() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      conflictId,
      payload,
    }: {
      conflictId: string;
      payload: ResolveSyncConflictPayload;
    }) => syncService.resolveConflict(conflictId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: syncQueryKeys.all });
    },
  });
}

export function useCreateSyncCheckpoint() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      deviceId,
      payload,
    }: {
      deviceId: string;
      payload: CreateSyncCheckpointPayload;
    }) => syncService.createCheckpoint(deviceId, payload),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: syncQueryKeys.checkpoints(variables.deviceId) }),
        queryClient.invalidateQueries({ queryKey: syncQueryKeys.status(variables.deviceId) }),
      ]);
    },
  });
}
