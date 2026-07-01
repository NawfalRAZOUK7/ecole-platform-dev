import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useTimetableClasses,
  useWeeklyTimetable,
  useTimetableSlots,
  useCreateTimetableSlot,
  useUpdateTimetableSlot,
  useDeleteTimetableSlot,
  useTimetableExceptions,
  useCreateTimetableException,
  useTimetableConstraints,
  useSaveConstraints,
  useTriggerGeneration,
  useGenerationJob,
  useGenerationPreview,
  useApplyGeneration,
  useClassWeeklyTimetable,
  useTeacherWeeklyTimetable,
  useMyWeeklyTimetable,
  timetableQueryKeys,
} from '@/features/academic/timetable/model/useTimetable';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) =>
    QueryClientProvider({ client: queryClient, children });
}

function apiResponse<T>(data: T) {
  return HttpResponse.json({
    data,
    meta: { timestamp: new Date().toISOString(), version: 'test' },
  });
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

function apiErrorResponse() {
  return HttpResponse.json(
    {
      error: {
        code: 'ERR-SYS-500',
        message: 'fail',
        category: 'system',
        retryable: false,
        timestamp: new Date().toISOString(),
      },
    },
    { status: 500 },
  );
}

const mockWeekly = {
  academic_year_id: 'ay1',
  week_start: '2026-09-01',
  week_end: '2026-09-07',
  slots: [
    {
      id: 'slot-1',
      day_of_week: 1,
      start_time: '08:00',
      end_time: '09:00',
      subject: 'Math',
      teacher_id: 't1',
      room: 'A1',
      is_recurring: true,
      class_id: 'c1',
    },
  ],
};

describe('timetableQueryKeys', () => {
  it('generates correct keys', () => {
    expect(timetableQueryKeys.all).toEqual(['timetable']);
    expect(timetableQueryKeys.classes()).toEqual(['timetable', 'classes']);
    expect(timetableQueryKeys.myWeekly()).toEqual(['timetable', 'my-weekly']);
    expect(timetableQueryKeys.classWeekly('c1')).toEqual(['timetable', 'class-weekly', 'c1']);
    expect(timetableQueryKeys.teacherWeekly('t1')).toEqual(['timetable', 'teacher-weekly', 't1']);
    expect(timetableQueryKeys.generationJob('j1')).toEqual(['timetable', 'job', 'j1']);
    expect(timetableQueryKeys.generationPreview('j1')).toEqual(['timetable', 'preview', 'j1']);
  });
});

describe('useTimetableClasses', () => {
  it('fetches classes when enabled', async () => {
    server.use(
      http.get('/api/v1/teacher/classes', () =>
        apiListResponse([{ id: 'c1', code: '6A', name: 'Class 6A' }]),
      ),
    );
    const { result } = renderHook(() => useTimetableClasses(true), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
  });

  it('does not fetch when disabled', () => {
    const { result } = renderHook(() => useTimetableClasses(false), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/teacher/classes', () => apiErrorResponse()));
    const { result } = renderHook(() => useTimetableClasses(true), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useWeeklyTimetable', () => {
  it('fetches me/weekly when not admin', async () => {
    server.use(http.get('/api/v1/timetable/me/weekly', () => apiResponse(mockWeekly)));
    const { result } = renderHook(() => useWeeklyTimetable(null, false), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.slots).toHaveLength(1);
  });

  it('fetches class weekly when admin with classId', async () => {
    server.use(http.get('/api/v1/timetable/class/:classId/weekly', () => apiResponse(mockWeekly)));
    const { result } = renderHook(() => useWeeklyTimetable('c1', true), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('is idle when admin but no classId', () => {
    const { result } = renderHook(() => useWeeklyTimetable(null, true), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useTimetableSlots', () => {
  it('fetches slots', async () => {
    server.use(http.get('/api/v1/timetable/slots', () => apiListResponse([mockWeekly.slots[0]])));
    const { result } = renderHook(() => useTimetableSlots({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
  });

  it('is idle when disabled', () => {
    const { result } = renderHook(() => useTimetableSlots({}, false), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateTimetableSlot', () => {
  it('creates a slot', async () => {
    server.use(
      http.post('/api/v1/timetable/slots', () => apiResponse(mockWeekly.slots[0])),
      http.get('/api/v1/timetable/slots', () => apiListResponse([])),
      http.get('/api/v1/timetable/me/weekly', () => apiResponse(mockWeekly)),
    );
    const { result } = renderHook(() => useCreateTimetableSlot(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        day_of_week: 1,
        start_time: '08:00',
        end_time: '09:00',
        subject: 'Math',
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useUpdateTimetableSlot', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useUpdateTimetableSlot(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useDeleteTimetableSlot', () => {
  it('deletes a slot', async () => {
    server.use(
      http.delete('/api/v1/timetable/slots/:slotId', () =>
        apiResponse({ id: 'slot-1', deleted: true }),
      ),
      http.get('/api/v1/timetable/slots', () => apiListResponse([])),
    );
    const { result } = renderHook(() => useDeleteTimetableSlot(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync('slot-1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useTimetableExceptions', () => {
  it('fetches exceptions', async () => {
    server.use(
      http.get('/api/v1/timetable/exceptions', () =>
        apiListResponse([
          {
            id: 'ex1',
            timetable_slot_id: 'slot-1',
            school_id: 's1',
            exception_date: '2026-10-01',
            exception_type: 'cancelled',
            substitute_teacher_id: null,
            new_room: null,
            reason: null,
            created_at: '2026-09-01',
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useTimetableExceptions({}), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].id).toBe('ex1');
  });

  it('is idle when disabled', () => {
    const { result } = renderHook(() => useTimetableExceptions({}, false), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateTimetableException', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateTimetableException(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });
});

describe('useTimetableConstraints', () => {
  it('fetches constraints', async () => {
    server.use(http.get('/api/v1/timetable/constraints', () => apiListResponse([])));
    const { result } = renderHook(() => useTimetableConstraints('ay1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.academic_year_id).toBe('ay1');
  });
});

describe('useSaveConstraints', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useSaveConstraints(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useTriggerGeneration', () => {
  it('triggers generation', async () => {
    server.use(
      http.post('/api/v1/timetable/generate', () =>
        apiResponse({
          job_id: 'job-1',
          status: 'pending',
          progress: 0,
          error: null,
          created_at: '2026-09-01',
        }),
      ),
    );
    const { result } = renderHook(() => useTriggerGeneration(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync('ay1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.job_id).toBe('job-1');
  });
});

describe('useGenerationJob', () => {
  it('fetches job when enabled with jobId', async () => {
    server.use(
      http.get('/api/v1/timetable/generate/:jobId', () =>
        apiResponse({
          job_id: 'job-1',
          status: 'completed',
          progress: 100,
          error: null,
          created_at: '2026-09-01',
        }),
      ),
    );
    const { result } = renderHook(() => useGenerationJob('job-1', true), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.status).toBe('completed');
  });

  it('is idle when disabled', () => {
    const { result } = renderHook(() => useGenerationJob('job-1', false), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useGenerationPreview', () => {
  it('fetches preview when enabled', async () => {
    server.use(
      http.get('/api/v1/timetable/generate/:jobId/preview', () =>
        apiResponse({ job_id: 'job-1', slots: [], warnings: [] }),
      ),
    );
    const { result } = renderHook(() => useGenerationPreview('job-1', true), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useApplyGeneration', () => {
  it('applies generation', async () => {
    server.use(
      http.post('/api/v1/timetable/generate/:jobId/apply', () =>
        apiResponse({ applied: 10, skipped: 0 }),
      ),
      http.get('/api/v1/timetable/slots', () => apiListResponse([])),
    );
    const { result } = renderHook(() => useApplyGeneration(), { wrapper: createWrapper() });
    await act(async () => {
      const data = await result.current.mutateAsync('job-1');
      expect(data.applied).toBe(10);
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useClassWeeklyTimetable', () => {
  it('fetches class weekly timetable', async () => {
    server.use(http.get('/api/v1/timetable/class/:classId/weekly', () => apiResponse(mockWeekly)));
    const { result } = renderHook(() => useClassWeeklyTimetable('c1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.academic_year_id).toBe('ay1');
  });

  it('is idle when disabled', () => {
    const { result } = renderHook(() => useClassWeeklyTimetable('c1', false), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useTeacherWeeklyTimetable', () => {
  it('fetches teacher weekly', async () => {
    server.use(
      http.get('/api/v1/timetable/teacher/:teacherId/weekly', () => apiResponse(mockWeekly)),
    );
    const { result } = renderHook(() => useTeacherWeeklyTimetable('t1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useMyWeeklyTimetable', () => {
  it('fetches my weekly timetable', async () => {
    server.use(http.get('/api/v1/timetable/me/weekly', () => apiResponse(mockWeekly)));
    const { result } = renderHook(() => useMyWeeklyTimetable(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.slots).toHaveLength(1);
  });
});
