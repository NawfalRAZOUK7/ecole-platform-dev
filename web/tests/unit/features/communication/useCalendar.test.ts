import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useCalendarEvents,
  useCalendarOptions,
  useCalendarEvent,
  useCreateCalendarEvent,
  useUpdateCalendarEvent,
  useDeleteCalendarEvent,
  useCalendarEventRsvp,
  useEventRSVPs,
  useHolidays,
  useCreateHoliday,
  useUpdateHoliday,
  useDeleteHoliday,
  useUpdateReminderPreferences,
} from '@/features/communication/calendar/model/useCalendar';

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

const mockEvent = {
  id: 'evt-1',
  instance_id: 'inst-1',
  school_id: 'sch-1',
  title_fr: 'Réunion',
  title_ar: null,
  title_en: null,
  description: 'Test event',
  type: 'meeting',
  visibility: 'school',
  start_at: '2026-09-10T09:00:00Z',
  end_at: '2026-09-10T11:00:00Z',
  is_all_day: false,
  location: null,
  capacity: null,
  class_id: null,
  role_codes: [],
  recurrence_rule: null,
  created_by: 'user-1',
  created_at: '2026-01-01T00:00:00Z',
};

const mockHoliday = {
  id: 'hol-1',
  name: 'Eid al-Adha',
  start_date: '2026-07-09',
  end_date: '2026-07-12',
  type: 'national' as const,
  description: null,
};

const defaultFilters = {
  from: '2026-09-01',
  to: '2026-09-30',
};

describe('useCalendarEvents', () => {
  it('returns events on success', async () => {
    server.use(http.get('/api/v1/events', () => apiListResponse([mockEvent])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCalendarEvents(defaultFilters), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data).toEqual([mockEvent]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/events', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCalendarEvents(defaultFilters), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCalendarOptions', () => {
  it('returns options on success', async () => {
    const opts = { classes: [], reminder_offsets: [60, 1440] };
    server.use(http.get('/api/v1/calendar/options', () => apiResponse(opts)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCalendarOptions(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(opts);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/calendar/options', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCalendarOptions(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCalendarEvent', () => {
  it('returns event detail', async () => {
    server.use(http.get('/api/v1/events/evt-1', () => apiResponse(mockEvent)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCalendarEvent('evt-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockEvent);
  });

  it('does not fetch when eventId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCalendarEvent(null), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('respects enabled option', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCalendarEvent('evt-1', { enabled: false }), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateCalendarEvent', () => {
  it('creates event and returns data', async () => {
    server.use(
      http.post('/api/v1/events', () => apiResponse(mockEvent)),
      http.get('/api/v1/events', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateCalendarEvent(), { wrapper });
    act(() => {
      result.current.mutate({
        title_fr: 'New Event',
        type: 'meeting',
        start_at: '2026-09-10T09:00:00Z',
        end_at: '2026-09-10T11:00:00Z',
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockEvent);
  });

  it('handles error', async () => {
    server.use(http.post('/api/v1/events', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateCalendarEvent(), { wrapper });
    act(() => result.current.mutate({ title_fr: 'Test' }));
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useUpdateCalendarEvent', () => {
  it('updates event successfully', async () => {
    const updated = { ...mockEvent, title_fr: 'Réunion mise à jour' };
    server.use(
      http.put('/api/v1/events/evt-1', () => apiResponse(updated)),
      http.get('/api/v1/events', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateCalendarEvent(), { wrapper });
    act(() => {
      result.current.mutate({ id: 'evt-1', payload: { title_fr: 'Réunion mise à jour' } });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(updated);
  });
});

describe('useDeleteCalendarEvent', () => {
  it('deletes event and returns id', async () => {
    server.use(
      http.delete('/api/v1/events/evt-1', () => apiResponse(null)),
      http.get('/api/v1/events', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useDeleteCalendarEvent(), { wrapper });
    act(() => result.current.mutate('evt-1'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe('evt-1');
  });
});

describe('useCalendarEventRsvp', () => {
  it('submits RSVP successfully', async () => {
    server.use(
      http.post('/api/v1/events/evt-1/rsvp', () => apiResponse(null)),
      http.get('/api/v1/events', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCalendarEventRsvp(), { wrapper });
    act(() => result.current.mutate({ id: 'evt-1', status: 'attending' }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useEventRSVPs', () => {
  it('returns RSVPs for an event', async () => {
    const rsvps = [{ user_id: 'u-1', status: 'attending', responded_at: '2026-09-01T00:00:00Z' }];
    server.use(http.get('/api/v1/events/evt-1/rsvps', () => apiResponse(rsvps)));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useEventRSVPs('evt-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(rsvps);
  });

  it('does not fetch when eventId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useEventRSVPs(null), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useHolidays', () => {
  it('returns holidays on success', async () => {
    server.use(http.get('/api/v1/calendar/holidays', () => apiResponse([mockHoliday])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useHolidays(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockHoliday]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/calendar/holidays', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useHolidays(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCreateHoliday', () => {
  it('creates a holiday', async () => {
    server.use(
      http.post('/api/v1/calendar/holidays', () => apiResponse(mockHoliday)),
      http.get('/api/v1/calendar/holidays', () => apiResponse([])),
      http.get('/api/v1/events', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateHoliday(), { wrapper });
    act(() => {
      result.current.mutate({
        name: 'Eid',
        start_date: '2026-07-09',
        end_date: '2026-07-12',
        type: 'national',
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockHoliday);
  });
});

describe('useUpdateHoliday', () => {
  it('updates a holiday', async () => {
    const updated = { ...mockHoliday, name: 'Updated Holiday' };
    server.use(
      http.put('/api/v1/calendar/holidays/hol-1', () => apiResponse(updated)),
      http.get('/api/v1/calendar/holidays', () => apiResponse([])),
      http.get('/api/v1/events', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateHoliday(), { wrapper });
    act(() => {
      result.current.mutate({
        id: 'hol-1',
        payload: {
          name: 'Updated Holiday',
          start_date: '2026-07-09',
          end_date: '2026-07-12',
          type: 'national',
        },
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useDeleteHoliday', () => {
  it('deletes a holiday', async () => {
    server.use(
      http.delete('/api/v1/calendar/holidays/hol-1', () => apiResponse(null)),
      http.get('/api/v1/calendar/holidays', () => apiResponse([])),
      http.get('/api/v1/events', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useDeleteHoliday(), { wrapper });
    act(() => result.current.mutate('hol-1'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useUpdateReminderPreferences', () => {
  it('updates reminder preferences', async () => {
    const prefs = [{ offset_minutes: 60, enabled: true }];
    server.use(
      http.post('/api/v1/events/reminder-preferences', () => apiResponse(prefs)),
      http.get('/api/v1/calendar/options', () => apiResponse({})),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateReminderPreferences(), { wrapper });
    act(() => result.current.mutate(prefs));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});
