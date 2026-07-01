import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useSubmissionAssignments,
  useCreateStudentSubmission,
  useUploadSubmissionFile,
  useFinalizeStudentSubmission,
  useUploadExercisePdf,
  useDownloadExercisePdf,
  useOverridePenalty,
  useUploadSubmissionFiles,
  usePreviewSubmission,
  submissionsQueryKeys,
} from '@/features/lms/submissions/model/useSubmissions';

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

describe('submissionsQueryKeys', () => {
  it('generates correct keys', () => {
    expect(submissionsQueryKeys.all).toEqual(['student-submissions']);
    expect(submissionsQueryKeys.assignments()).toEqual(['student-submissions', 'assignments']);
  });
});

describe('useSubmissionAssignments', () => {
  it('fetches assignments', async () => {
    server.use(
      http.get('/api/v1/assignments', () =>
        apiListResponse([
          { id: 'a1', title: 'HW 1', course_id: 'c1', due_at: null, total_points: 10 },
        ]),
      ),
    );
    const { result } = renderHook(() => useSubmissionAssignments(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data![0].id).toBe('a1');
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/assignments', () => apiErrorResponse()));
    const { result } = renderHook(() => useSubmissionAssignments(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCreateStudentSubmission', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateStudentSubmission(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('creates a submission', async () => {
    server.use(http.post('/api/v1/submissions', () => apiResponse({ id: 'sub1' })));
    const { result } = renderHook(() => useCreateStudentSubmission(), { wrapper: createWrapper() });
    await act(async () => {
      const data = await result.current.mutateAsync('a1');
      expect(data.id).toBe('sub1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useUploadSubmissionFile', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useUploadSubmissionFile(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useFinalizeStudentSubmission', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useFinalizeStudentSubmission(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });

  it('finalizes a submission', async () => {
    server.use(http.post('/api/v1/submissions/:id/submit', () => apiResponse(null)));
    const { result } = renderHook(() => useFinalizeStudentSubmission(), {
      wrapper: createWrapper(),
    });
    await act(async () => {
      await result.current.mutateAsync('sub1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useUploadExercisePdf', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useUploadExercisePdf(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useDownloadExercisePdf', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useDownloadExercisePdf(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useOverridePenalty', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useOverridePenalty(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('overrides penalty', async () => {
    server.use(http.post('/api/v1/submissions/:id/override-penalty', () => apiResponse(null)));
    const { result } = renderHook(() => useOverridePenalty(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        submissionId: 'sub1',
        payload: { penalty_override: 0, reason: 'Technical issue' },
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useUploadSubmissionFiles', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useUploadSubmissionFiles(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('usePreviewSubmission', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => usePreviewSubmission('sub1'), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('fetches submission preview', async () => {
    server.use(
      http.get('/api/v1/submissions/:id/preview', () =>
        apiResponse({ preview_url: 'https://example.com/preview', status: 'ready' }),
      ),
      http.get('/api/v1/assignments', () => apiListResponse([])),
    );
    const { result } = renderHook(() => usePreviewSubmission('sub1'), { wrapper: createWrapper() });
    await act(async () => {
      const data = await result.current.mutateAsync();
      expect(data.status).toBe('ready');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});
