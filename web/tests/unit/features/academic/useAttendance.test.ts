import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useClassAttendance,
  useMarkAttendance,
  useSubmitJustification,
  useAttendanceTrends,
  useAttendanceAlerts,
  useStudentHistory,
  useSubmitJustificationDirect,
  useReviewJustification,
  useCheckAttendanceThresholds,
  attendanceQueryKeys,
} from '@/features/academic/attendance/model/useAttendance';

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

const mockRecord = {
  id: 'rec1',
  student_id: 'stu1',
  student_name: 'Alice',
  class_id: 'c1',
  date: '2026-04-01',
  status: 'present' as const,
  justified: false,
  marked_by: 'teacher-1',
};

describe('attendanceQueryKeys', () => {
  it('generates correct query keys', () => {
    expect(attendanceQueryKeys.all).toEqual(['attendance']);
    expect(attendanceQueryKeys.classAttendance('c1', '2026-04-01')).toEqual([
      'attendance',
      'class',
      'c1',
      '2026-04-01',
    ]);
    expect(attendanceQueryKeys.trends('c1', '2026-01-01', '2026-06-30')).toEqual([
      'attendance',
      'trends',
      'c1',
      '2026-01-01',
      '2026-06-30',
    ]);
    expect(attendanceQueryKeys.alerts('s1')).toEqual(['attendance', 'alerts', 's1', 'all']);
    expect(attendanceQueryKeys.alerts('s1', 'p1')).toEqual(['attendance', 'alerts', 's1', 'p1']);
    expect(attendanceQueryKeys.studentHistory('stu1')).toEqual(['attendance', 'student', 'stu1']);
  });
});

describe('useClassAttendance', () => {
  it('fetches attendance records', async () => {
    server.use(
      http.get('/api/v1/attendance/class/:classId', () =>
        apiResponse({
          class_id: 'c1',
          stats: { total_students: 1, attendance_rate: 100, absent_count: 0, late_count: 0 },
          records: [mockRecord],
        }),
      ),
    );
    const { result } = renderHook(() => useClassAttendance('c1', '2026-04-01'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data![0].student_id).toBe('stu1');
  });

  it('does not fetch when classId is empty', () => {
    const { result } = renderHook(() => useClassAttendance('', '2026-04-01'), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('does not fetch when date is empty', () => {
    const { result } = renderHook(() => useClassAttendance('c1', ''), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/attendance/class/:classId', () => apiErrorResponse()));
    const { result } = renderHook(() => useClassAttendance('c1', '2026-04-01'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useMarkAttendance', () => {
  it('marks attendance with optimistic update', async () => {
    server.use(
      http.post('/api/v1/attendance/class/:classId', () => apiResponse(null)),
      http.get('/api/v1/attendance/class/:classId', () =>
        apiResponse({
          class_id: 'c1',
          stats: { total_students: 1, attendance_rate: 100, absent_count: 0, late_count: 0 },
          records: [mockRecord],
        }),
      ),
    );
    const { result } = renderHook(() => useMarkAttendance(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        class_id: 'c1',
        date: '2026-04-01',
        records: [{ student_id: 'stu1', status: 'present', note: undefined }],
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('is idle initially', () => {
    const { result } = renderHook(() => useMarkAttendance(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useSubmitJustification', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useSubmitJustification(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useAttendanceTrends', () => {
  it('fetches trends when all params provided', async () => {
    server.use(
      http.get('/api/v1/analytics/attendance/trends/:classId', () =>
        apiResponse([{ date: '2026-04-01', attendance_rate: 95, absent_count: 1, late_count: 0 }]),
      ),
    );
    const { result } = renderHook(
      () => useAttendanceTrends('c1', { from: '2026-01-01', to: '2026-06-30' }),
      { wrapper: createWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
  });

  it('is idle when classId is empty', () => {
    const { result } = renderHook(
      () => useAttendanceTrends('', { from: '2026-01-01', to: '2026-06-30' }),
      { wrapper: createWrapper() },
    );
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useAttendanceAlerts', () => {
  it('fetches alerts for a school', async () => {
    server.use(
      http.get('/api/v1/analytics/attendance/alerts', () =>
        apiResponse([
          {
            student_id: 'stu1',
            student_name: 'Alice',
            class_id: 'c1',
            attendance_rate: 60,
            threshold: 75,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useAttendanceAlerts('school-1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
  });

  it('is idle when schoolId is empty', () => {
    const { result } = renderHook(() => useAttendanceAlerts(''), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useStudentHistory', () => {
  it('fetches student attendance history', async () => {
    server.use(
      http.get('/api/v1/analytics/attendance/student/:studentId', () => apiResponse([mockRecord])),
    );
    const { result } = renderHook(() => useStudentHistory('stu1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
  });

  it('is idle when studentId is empty', () => {
    const { result } = renderHook(() => useStudentHistory(''), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useSubmitJustificationDirect', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useSubmitJustificationDirect(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });
});

describe('useReviewJustification', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useReviewJustification(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('reviews a justification', async () => {
    server.use(
      http.post('/api/v1/attendance/justifications/:id/review', () =>
        apiResponse({ id: 'j1', status: 'approved' }),
      ),
      http.get('/api/v1/attendance/class/:classId', () =>
        apiResponse({
          class_id: 'c1',
          stats: { total_students: 0, attendance_rate: 100, absent_count: 0, late_count: 0 },
          records: [],
        }),
      ),
    );
    const { result } = renderHook(() => useReviewJustification(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        justificationId: 'j1',
        payload: { status: 'approved', reviewer_note: null },
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useCheckAttendanceThresholds', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCheckAttendanceThresholds(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });

  it('checks thresholds', async () => {
    server.use(
      http.post('/api/v1/analytics/attendance/check-thresholds', () =>
        apiResponse([
          {
            class_id: 'c1',
            student_id: 'stu1',
            attendance_rate: 60,
            threshold: 75,
            triggered: true,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useCheckAttendanceThresholds(), {
      wrapper: createWrapper(),
    });
    await act(async () => {
      const data = await result.current.mutateAsync();
      expect(data).toHaveLength(1);
      expect(data[0].triggered).toBe(true);
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});
