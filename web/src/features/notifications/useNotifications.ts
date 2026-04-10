import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
  type InfiniteData,
} from '@tanstack/react-query';
import type { ApiListResponse } from '@/services/api/client';
import { STALE_NOTIFICATIONS } from '@/shared/hooks/useQueryDefaults';
import {
  notificationsService,
  type BatchNotifyPayload,
  type NotificationListFilters,
  type NotificationPreferencesUpdatePayload,
  type NotificationSettingsInput,
  type RegisterDevicePayload,
} from './notifications.service';
import type {
  DeviceItem,
  NotificationDigestResponse,
  NotificationItem,
  NotificationPreference,
} from './types';

type NotificationPages = InfiniteData<ApiListResponse<NotificationItem>, string | undefined>;

export const notificationQueryKeys = {
  all: ['notifications'] as const,
  lists: () => [...notificationQueryKeys.all, 'list'] as const,
  list: (filters: NotificationListFilters) => [...notificationQueryKeys.lists(), filters] as const,
  preferences: () => [...notificationQueryKeys.all, 'preferences'] as const,
  digest: () => [...notificationQueryKeys.all, 'digest'] as const,
  devices: () => [...notificationQueryKeys.all, 'devices'] as const,
  unreadCount: () => [...notificationQueryKeys.all, 'unread-count'] as const,
};

function mapNotificationPages(
  data: NotificationPages | undefined,
  transform: (item: NotificationItem) => NotificationItem,
): NotificationPages | undefined {
  if (!data) {
    return data;
  }

  return {
    pageParams: data.pageParams,
    pages: data.pages.map((page) => ({
      ...page,
      data: page.data.map(transform),
    })),
  };
}

export function useNotifications(filters: NotificationListFilters) {
  return useInfiniteQuery({
    queryKey: notificationQueryKeys.list(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      notificationsService.list({
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_NOTIFICATIONS,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, read }: { id: string; read: boolean }) =>
      (await notificationsService.markRead(id, read)).data,
    onSuccess: (_notification, variables) => {
      queryClient.setQueriesData<NotificationPages>(
        { queryKey: notificationQueryKeys.lists() },
        (current) =>
          mapNotificationPages(current, (item) =>
            item.id === variables.id
              ? {
                  ...item,
                  is_read: variables.read,
                  read_at: variables.read ? new Date().toISOString() : null,
                }
              : item,
          ),
      );
      void queryClient.invalidateQueries({ queryKey: notificationQueryKeys.lists() });
    },
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      await notificationsService.markAllRead();
    },
    onSuccess: () => {
      queryClient.setQueriesData<NotificationPages>(
        { queryKey: notificationQueryKeys.lists() },
        (current) =>
          mapNotificationPages(current, (item) => ({
            ...item,
            is_read: true,
            read_at: item.read_at || new Date().toISOString(),
          })),
      );
      void queryClient.invalidateQueries({ queryKey: notificationQueryKeys.lists() });
    },
  });
}

export function useNotificationPreferences() {
  return useQuery({
    queryKey: notificationQueryKeys.preferences(),
    queryFn: async () => (await notificationsService.getPreferences()).data.preferences,
    staleTime: STALE_NOTIFICATIONS,
  });
}

export function useNotificationDigestPreferences() {
  return useQuery({
    queryKey: notificationQueryKeys.digest(),
    queryFn: async () => (await notificationsService.getDigestPreferences()).data,
    staleTime: STALE_NOTIFICATIONS,
  });
}

export function useNotificationDevices() {
  return useQuery({
    queryKey: notificationQueryKeys.devices(),
    queryFn: async () => (await notificationsService.listDevices()).data,
    staleTime: STALE_NOTIFICATIONS,
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: NotificationPreferencesUpdatePayload) => {
      await notificationsService.updateNotificationPreferences(payload);
      return payload.preferences;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: notificationQueryKeys.preferences() });
    },
  });
}

export function useSaveNotificationSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ preferences, digestFrequency }: NotificationSettingsInput) => {
      const consents = (await notificationsService.listConsents()).data;
      const consentUpdates = preferences.flatMap((preference) => {
        const nextStatus = preference.enabled ? 'opted_in' : 'opted_out';
        return consents
          .filter(
            (consent) =>
              consent.topic === preference.category &&
              consent.channel === preference.channel &&
              consent.status !== nextStatus,
          )
          .map((consent) => notificationsService.updateConsent(consent.id, nextStatus));
      });

      await Promise.all([
        notificationsService.updateNotificationPreferences({ preferences }),
        notificationsService.updateDigestPreferences(digestFrequency),
        ...consentUpdates,
      ]);
      return { preferences, digestFrequency };
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: notificationQueryKeys.preferences() }),
        queryClient.invalidateQueries({ queryKey: notificationQueryKeys.digest() }),
      ]);
    },
  });
}

export function useRemoveNotificationDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (deviceId: string) => {
      await notificationsService.removeDevice(deviceId);
      return deviceId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: notificationQueryKeys.devices() });
    },
  });
}

export function useRegisterDevice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: RegisterDevicePayload) =>
      (await notificationsService.registerDevice(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: notificationQueryKeys.devices() });
    },
  });
}

export function useNotificationUnreadCount() {
  return useQuery({
    queryKey: notificationQueryKeys.unreadCount(),
    queryFn: async () => (await notificationsService.getUnreadCount()).data,
    staleTime: STALE_NOTIFICATIONS,
  });
}

export function useBatchNotify() {
  return useMutation({
    mutationFn: async (payload: BatchNotifyPayload) => {
      await notificationsService.batchNotify(payload);
    },
  });
}

export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (notificationId: string) => {
      await notificationsService.deleteNotification(notificationId);
      return notificationId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: notificationQueryKeys.lists() });
      await queryClient.invalidateQueries({ queryKey: notificationQueryKeys.unreadCount() });
    },
  });
}

export type NotificationPreferencesQueryData = NotificationPreference[];
export type NotificationDigestQueryData = NotificationDigestResponse;
export type NotificationDevicesQueryData = DeviceItem[];
