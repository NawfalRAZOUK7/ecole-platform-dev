import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useNotifications,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
  useNotificationPreferences,
  useNotificationDigestPreferences,
  useNotificationDevices,
  useUpdateNotificationPreferences,
  useRemoveNotificationDevice,
  useRegisterDevice,
  useNotificationUnreadCount,
  useBatchNotify,
  useDeleteNotification,
} from '@/features/communication/notifications/model/useNotifications';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) =>
    QueryClientProvider({ client: queryClient, children });
}

function apiListResponse<T>(data: T[]) {
  return HttpResponse.json({
    data,
    meta: {
      next_cursor: null,
      has_more: false,
      timestamp: new Date().toISOString(),
      version: 'test',
    },
  });
}

function apiResponse<T>(data: T) {
  return HttpResponse.json({
    data,
    meta: { timestamp: new Date().toISOString(), version: 'test' },
  });
}

function apiError(status = 500) {
  return HttpResponse.json(
    {
      error: { code: 'ERR', message: 'fail', category: 'system', retryable: false, timestamp: '' },
    },
    { status },
  );
}

const mockNotification = {
  id: 'notif-1',
  user_id: 'user-1',
  category: 'attendance',
  channel: 'in_app',
  title: 'Absence signalée',
  body: 'Votre enfant est absent',
  action_url: null,
  is_read: false,
  read_at: null,
  created_at: '2026-09-10T08:00:00Z',
};

const mockPreference = {
  category: 'attendance',
  channel: 'in_app',
  enabled: true,
};

const mockDevice = {
  id: 'dev-1',
  token: 'fcm-token-123',
  platform: 'android' as const,
  device_name: 'Phone',
  created_at: '2026-01-01T00:00:00Z',
};

describe('useNotifications', () => {
  it('returns notifications on success', async () => {
    server.use(http.get('/api/v1/notifications', () => apiListResponse([mockNotification])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useNotifications({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data).toEqual([mockNotification]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/notifications', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useNotifications({}), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it('accepts filters', async () => {
    server.use(http.get('/api/v1/notifications', () => apiListResponse([mockNotification])));
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useNotifications({ category: 'attendance', read: 'false' }),
      { wrapper },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useMarkNotificationRead', () => {
  it('marks notification as read', async () => {
    const readNotif = { ...mockNotification, is_read: true, read_at: '2026-09-10T09:00:00Z' };
    server.use(
      http.patch('/api/v1/notifications/notif-1/read', () => apiResponse(readNotif)),
      http.get('/api/v1/notifications', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useMarkNotificationRead(), { wrapper });
    act(() => result.current.mutate({ id: 'notif-1', read: true }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles error', async () => {
    server.use(http.patch('/api/v1/notifications/notif-1/read', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useMarkNotificationRead(), { wrapper });
    act(() => result.current.mutate({ id: 'notif-1', read: true }));
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useMarkAllNotificationsRead', () => {
  it('marks all notifications as read', async () => {
    server.use(
      http.patch('/api/v1/notifications/mark-all-read', () => apiResponse(null)),
      http.get('/api/v1/notifications', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useMarkAllNotificationsRead(), { wrapper });
    act(() => result.current.mutate());
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useNotificationPreferences', () => {
  it('returns preferences on success', async () => {
    server.use(
      http.get('/api/v1/notifications/preferences', () =>
        apiResponse({ preferences: [mockPreference] }),
      ),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useNotificationPreferences(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockPreference]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/notifications/preferences', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useNotificationPreferences(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useNotificationDigestPreferences', () => {
  it('returns digest preferences on success', async () => {
    const digest = { digest_frequency: 'daily', enabled: true };
    server.use(http.get('/api/v1/notifications/digest/preferences', () => apiResponse(digest)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useNotificationDigestPreferences(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(digest);
  });
});

describe('useNotificationDevices', () => {
  it('returns devices on success', async () => {
    server.use(http.get('/api/v1/devices', () => apiListResponse([mockDevice])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useNotificationDevices(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockDevice]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/devices', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useNotificationDevices(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useUpdateNotificationPreferences', () => {
  it('updates preferences successfully', async () => {
    server.use(
      http.put('/api/v1/notifications/preferences', () => apiResponse(null)),
      http.get('/api/v1/notifications/preferences', () => apiResponse({ preferences: [] })),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateNotificationPreferences(), { wrapper });
    act(() => result.current.mutate({ preferences: [mockPreference] }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useRemoveNotificationDevice', () => {
  it('removes device successfully', async () => {
    server.use(
      http.delete('/api/v1/devices/dev-1', () => apiResponse(null)),
      http.get('/api/v1/devices', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useRemoveNotificationDevice(), { wrapper });
    act(() => result.current.mutate('dev-1'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe('dev-1');
  });
});

describe('useRegisterDevice', () => {
  it('registers a device', async () => {
    server.use(
      http.post('/api/v1/devices/register', () => apiResponse(mockDevice)),
      http.get('/api/v1/devices', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useRegisterDevice(), { wrapper });
    act(() => result.current.mutate({ token: 'fcm-token-123', platform: 'android' }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockDevice);
  });
});

describe('useNotificationUnreadCount', () => {
  it('returns unread count on success', async () => {
    server.use(http.get('/api/v1/notifications/unread-count', () => apiResponse({ count: 5 })));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useNotificationUnreadCount(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ count: 5 });
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/notifications/unread-count', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useNotificationUnreadCount(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useBatchNotify', () => {
  it('sends batch notifications', async () => {
    server.use(http.post('/api/v1/notifications/batch', () => apiResponse(null)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBatchNotify(), { wrapper });
    act(() => {
      result.current.mutate({ user_ids: ['u-1', 'u-2'], title: 'Alert', body: 'Message' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles error', async () => {
    server.use(http.post('/api/v1/notifications/batch', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBatchNotify(), { wrapper });
    act(() => result.current.mutate({ user_ids: ['u-1'], title: 'Alert', body: 'Msg' }));
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useDeleteNotification', () => {
  it('deletes a notification', async () => {
    server.use(
      http.delete('/api/v1/notifications/notif-1', () => apiResponse(null)),
      http.get('/api/v1/notifications', () => apiListResponse([])),
      http.get('/api/v1/notifications/unread-count', () => apiResponse({ count: 0 })),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useDeleteNotification(), { wrapper });
    act(() => result.current.mutate('notif-1'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe('notif-1');
  });
});
