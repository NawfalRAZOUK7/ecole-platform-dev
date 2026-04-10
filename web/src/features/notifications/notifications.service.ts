import { api } from '@/services/api/client';
import type {
  ConsentItem,
  DeviceItem,
  NotificationDigestResponse,
  NotificationItem,
  NotificationPreference,
  NotificationPreferencesResponse,
} from './types';

export interface RegisterDevicePayload {
  token: string;
  platform: 'android' | 'ios' | 'web';
  device_name?: string;
}

export interface BatchNotifyPayload {
  user_ids: string[];
  title: string;
  body: string;
  category?: string;
  action_url?: string;
}

export interface NotificationListFilters extends Record<string, string | number | undefined> {
  limit?: number;
  cursor?: string;
  category?: string;
  channel?: string;
  read?: string;
  from?: string;
  to?: string;
}

export interface NotificationSettingsInput {
  preferences: NotificationPreference[];
  digestFrequency: string;
}

export interface NotificationPreferencesUpdatePayload {
  preferences: NotificationPreference[];
}

export const notificationsService = {
  list(params: NotificationListFilters) {
    return api.list<NotificationItem>('/notifications', params);
  },

  markRead(id: string, read: boolean) {
    return api.patch<NotificationItem>(`/notifications/${id}/read`, { read });
  },

  markAllRead() {
    return api.patch<void>('/notifications/mark-all-read', {});
  },

  getPreferences() {
    return api.get<NotificationPreferencesResponse>('/notifications/preferences');
  },

  updatePreferences(preferences: NotificationPreference[]) {
    return api.post<void>('/notifications/preferences', { preferences });
  },

  updateNotificationPreferences(payload: NotificationPreferencesUpdatePayload) {
    return api.put<void>('/notifications/preferences', payload);
  },

  getDigestPreferences() {
    return api.get<NotificationDigestResponse>('/notifications/digest/preferences');
  },

  updateDigestPreferences(digestFrequency: string) {
    return api.post<void>('/notifications/digest/preferences', {
      digest_frequency: digestFrequency,
    });
  },

  listConsents() {
    return api.get<ConsentItem[]>('/consents');
  },

  updateConsent(consentId: string, status: ConsentItem['status']) {
    return api.put<void>(`/consents/${consentId}`, { status });
  },

  listDevices() {
    return api.list<DeviceItem>('/devices');
  },

  removeDevice(deviceId: string) {
    return api.delete<void>(`/devices/${deviceId}`);
  },

  registerDevice(payload: RegisterDevicePayload) {
    return api.post<DeviceItem>('/devices/register', payload);
  },

  getUnreadCount() {
    return api.get<{ count: number }>('/notifications/unread-count');
  },

  batchNotify(payload: BatchNotifyPayload) {
    return api.post<void>('/notifications/batch', payload);
  },

  deleteNotification(notificationId: string) {
    return api.delete<void>(`/notifications/${notificationId}`);
  },
};
