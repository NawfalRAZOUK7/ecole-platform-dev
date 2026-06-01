import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useClassGradebook,
  useStudentGrades,
  useUpdateGrades,
  useWeightedSummary,
  useGradebookCategories,
  useCreateGradebookCategory,
  useComputeGrades,
  useGradebookTranscript,
  usePeriodGradebook,
  gradebookQueryKeys,
} from '@/features/academic/gradebook/model/useGradebook';

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

const mockGradebookResponse = {
  class_id: 'c1',
  class_name: 'Class 6A',
  categories: [{ id: 'cat1', name: 'Quiz', weight: 1 }],
  assignments: [
    {
      assignment_id: 'quiz-1',
      title: 'Quiz 1',
      category_id: 'cat1',
      total_points: 20,
      due_at: '2026-04-01',
    },
  ],
  rows: [
    {
      student_id: 'stu1',
      student_name: 'Alice',
      assignments: [{ assignment_id: 'quiz-1', score: 16 }],
      weighted_average: 16,
    },
  ],
};

describe('gradebookQueryKeys', () => {
  it('generates correct keys', () => {
    expect(gradebookQueryKeys.all).toEqual(['gradebook']);
    expect(gradebookQueryKeys.classGradebook('c1', 'p1')).toEqual([
      'gradebook',
      'class',
      'c1',
      'p1',
      'all',
    ]);
    expect(gradebookQueryKeys.classGradebook('c1', 'p1', 'prog1')).toEqual([
      'gradebook',
      'class',
      'c1',
      'p1',
      'prog1',
    ]);
    expect(gradebookQueryKeys.studentGrades('stu1')).toEqual(['gradebook', 'student', 'stu1']);
    expect(gradebookQueryKeys.transcript('stu1')).toEqual([
      'gradebook',
      'transcript',
      'stu1',
      'current',
    ]);
    expect(gradebookQueryKeys.transcript('stu1', 'ay1')).toEqual([
      'gradebook',
      'transcript',
      'stu1',
      'ay1',
    ]);
    expect(gradebookQueryKeys.weightedSummary('c1', 'p1')).toEqual([
      'gradebook',
      'weighted-summary',
      'c1',
      'p1',
    ]);
    expect(gradebookQueryKeys.categories('c1', 'p1')).toEqual([
      'gradebook',
      'categories',
      'c1',
      'p1',
    ]);
  });
});

describe('useClassGradebook', () => {
  it('fetches class gradebook', async () => {
    server.use(
      http.get('/api/v1/gradebook/:classId/:periodId', () => apiResponse(mockGradebookResponse)),
    );
    const { result } = renderHook(() => useClassGradebook('c1', 'p1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.class_id).toBe('c1');
    expect(result.current.data?.entries).toHaveLength(1);
  });

  it('is idle when classId is empty', () => {
    const { result } = renderHook(() => useClassGradebook('', 'p1'), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('is idle when periodId is empty', () => {
    const { result } = renderHook(() => useClassGradebook('c1', ''), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/gradebook/:classId/:periodId', () => apiErrorResponse()));
    const { result } = renderHook(() => useClassGradebook('c1', 'p1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useStudentGrades', () => {
  it('fetches student grades', async () => {
    server.use(
      http.get('/api/v1/gradebook/transcript/:studentId', () =>
        apiResponse({
          student_id: 'stu1',
          student_name: 'Alice',
          periods: [
            {
              class_id: 'c1',
              class_name: 'Class 6A',
              period_id: 'p1',
              period_label: 'Term 1',
              weighted_average: 16,
              class_rank: 1,
            },
          ],
        }),
      ),
    );
    const { result } = renderHook(() => useStudentGrades('stu1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.student_id).toBe('stu1');
    expect(result.current.data?.overall_average).toBe(16);
  });

  it('is idle when studentId is empty', () => {
    const { result } = renderHook(() => useStudentGrades(''), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useUpdateGrades', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useUpdateGrades(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('updates grades', async () => {
    server.use(
      http.get('/api/v1/gradebook/:classId/:periodId', () => apiResponse(mockGradebookResponse)),
    );
    const { result } = renderHook(() => useUpdateGrades(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        class_id: 'c1',
        period_id: 'p1',
        grades: [{ student_id: 'stu1', assignment_id: 'quiz-1', score: 18 }],
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useWeightedSummary', () => {
  it('computes weighted summary from gradebook', async () => {
    server.use(
      http.get('/api/v1/gradebook/:classId/:periodId', () => apiResponse(mockGradebookResponse)),
    );
    const { result } = renderHook(() => useWeightedSummary('c1', 'p1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.class_id).toBe('c1');
    expect(result.current.data?.class_average).toBe(16);
  });

  it('is idle when classId is empty', () => {
    const { result } = renderHook(() => useWeightedSummary('', 'p1'), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useGradebookCategories', () => {
  it('fetches categories', async () => {
    server.use(
      http.get('/api/v1/gradebook/categories/:classId/:periodId', () =>
        apiListResponse([{ id: 'cat1', class_id: 'c1', period_id: 'p1', name: 'Quiz', weight: 1 }]),
      ),
    );
    const { result } = renderHook(() => useGradebookCategories('c1', 'p1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].id).toBe('cat1');
  });

  it('is idle when ids are empty', () => {
    const { result } = renderHook(() => useGradebookCategories('', 'p1'), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateGradebookCategory', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateGradebookCategory(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useComputeGrades', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useComputeGrades(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('computes grades', async () => {
    server.use(
      http.post('/api/v1/gradebook/compute/:classId/:periodId', () =>
        apiResponse({
          class_id: 'c1',
          class_average: 16,
          pass_rate: 100,
          highest_average: 16,
          lowest_average: 16,
        }),
      ),
      http.get('/api/v1/gradebook/:classId/:periodId', () => apiResponse(mockGradebookResponse)),
    );
    const { result } = renderHook(() => useComputeGrades(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync({ classId: 'c1', periodId: 'p1' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useGradebookTranscript', () => {
  it('fetches transcript', async () => {
    server.use(
      http.get('/api/v1/gradebook/transcript/:studentId', () =>
        apiResponse({
          student_id: 'stu1',
          student_name: 'Alice',
          periods: [],
        }),
      ),
    );
    const { result } = renderHook(() => useGradebookTranscript('stu1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.student_id).toBe('stu1');
  });

  it('is idle when studentId is empty', () => {
    const { result } = renderHook(() => useGradebookTranscript(''), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('usePeriodGradebook', () => {
  it('fetches period gradebook', async () => {
    server.use(
      http.get('/api/v1/gradebook/:classId/:periodId', () => apiResponse(mockGradebookResponse)),
    );
    const { result } = renderHook(() => usePeriodGradebook('c1', 'p1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.class_id).toBe('c1');
  });

  it('is idle when classId is empty', () => {
    const { result } = renderHook(() => usePeriodGradebook('', 'p1'), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});
