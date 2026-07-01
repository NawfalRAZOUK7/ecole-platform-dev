import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useAnnouncements,
  useCreateAnnouncement,
  useUpdateAnnouncement,
  usePublishAnnouncement,
} from '@/features/communication/announcements/model/useAnnouncements';

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

const mockAnnouncement = {
  id: 'ann-1',
  school_id: 'sch-1',
  author_id: 'user-1',
  title: 'Rentrée scolaire 2026',
  body: 'La rentrée aura lieu le 1er septembre.',
  target_roles: ['PAR', 'STD'],
  target_class_ids: [],
  published_at: null,
  status: 'draft',
  created_at: '2026-08-01T00:00:00Z',
  updated_at: null,
};

describe('useAnnouncements', () => {
  it('returns announcements on success', async () => {
    server.use(http.get('/api/v1/announcements', () => apiListResponse([mockAnnouncement])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAnnouncements({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data).toEqual([mockAnnouncement]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/announcements', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAnnouncements({}), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it('accepts status filter', async () => {
    server.use(http.get('/api/v1/announcements', () => apiListResponse([mockAnnouncement])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAnnouncements({ status: 'published' }), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('paginates with hasNextPage', async () => {
    server.use(
      http.get('/api/v1/announcements', () =>
        HttpResponse.json({
          data: [mockAnnouncement],
          meta: {
            next_cursor: 'cursor-2',
            has_more: true,
            timestamp: new Date().toISOString(),
            version: 'test',
          },
        }),
      ),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useAnnouncements({}), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.hasNextPage).toBe(true);
  });
});

describe('useCreateAnnouncement', () => {
  it('creates an announcement', async () => {
    server.use(
      http.post('/api/v1/announcements', () => apiResponse(null)),
      http.get('/api/v1/announcements', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateAnnouncement(), { wrapper });
    act(() => {
      result.current.mutate({
        title: 'New Announcement',
        body: 'Content here',
        target_roles: ['PAR'],
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles error', async () => {
    server.use(http.post('/api/v1/announcements', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateAnnouncement(), { wrapper });
    act(() => result.current.mutate({ title: 'Test', body: 'Body', target_roles: [] }));
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useUpdateAnnouncement', () => {
  it('updates an announcement', async () => {
    server.use(
      http.put('/api/v1/announcements/ann-1', () => apiResponse(null)),
      http.get('/api/v1/announcements', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateAnnouncement(), { wrapper });
    act(() => {
      result.current.mutate({
        announcementId: 'ann-1',
        payload: { title: 'Updated', body: 'Updated body', target_roles: ['PAR'] },
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles error', async () => {
    server.use(http.put('/api/v1/announcements/ann-1', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateAnnouncement(), { wrapper });
    act(() =>
      result.current.mutate({
        announcementId: 'ann-1',
        payload: { title: 'X', body: 'Y', target_roles: [] },
      }),
    );
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('usePublishAnnouncement', () => {
  it('publishes an announcement', async () => {
    server.use(
      http.post('/api/v1/announcements/ann-1/publish', () => apiResponse(null)),
      http.get('/api/v1/announcements', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePublishAnnouncement(), { wrapper });
    act(() => result.current.mutate('ann-1'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles error', async () => {
    server.use(http.post('/api/v1/announcements/ann-1/publish', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePublishAnnouncement(), { wrapper });
    act(() => result.current.mutate('ann-1'));
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
