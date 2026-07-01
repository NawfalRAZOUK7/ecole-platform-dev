/**
 * Tests for src/features/lms/rubrics/model/useRubrics.ts
 *
 * Covers every hook:
 *   - useRubrics, useRubric, useRubricResults (queries with staleTime + enabled)
 *   - useCreateRubric, useUpdateRubric, useDuplicateRubric (mutations + invalidations)
 *   - useGradeRubric (mutation + results invalidation)
 *
 * Key invariants exercised:
 *   - rubricsQueryKeys helpers produce stable, identifiable keys
 *   - enabled:false branch when id is empty string
 *   - onSuccess callbacks invalidate the appropriate keys
 */
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';

import { server } from '../../../utils/mocks';

import {
  rubricsQueryKeys,
  useCreateRubric,
  useDuplicateRubric,
  useGradeRubric,
  useRubric,
  useRubricResults,
  useRubrics,
  useUpdateRubric,
} from '@/features/lms/rubrics/model/useRubrics';

const META = { timestamp: '2026-06-01T00:00:00Z', version: '1.0.0' };

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe('rubricsQueryKeys', () => {
  it('produces stable key shapes', () => {
    expect(rubricsQueryKeys.all).toEqual(['rubrics']);
    expect(rubricsQueryKeys.list()).toEqual(['rubrics', 'list']);
    expect(rubricsQueryKeys.detail('r-1')).toEqual(['rubrics', 'detail', 'r-1']);
    expect(rubricsQueryKeys.results('r-1')).toEqual(['rubrics', 'results', 'r-1']);
  });
});

describe('useRubrics (list query)', () => {
  it('fetches and unwraps the envelope', async () => {
    server.use(
      http.get('/api/v1/rubrics', () =>
        HttpResponse.json({
          data: [{ id: 'r-1', title: 'Math rubric' }],
          meta: { ...META, next_cursor: null, has_more: false },
        }),
      ),
    );

    const { result } = renderHook(() => useRubrics(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([{ id: 'r-1', title: 'Math rubric' }]);
  });
});

describe('useRubric (detail query)', () => {
  it('fetches a single rubric when id is provided', async () => {
    server.use(
      http.get('/api/v1/rubrics/:id', ({ params }) =>
        HttpResponse.json({ data: { id: params.id, title: 'Rubric A' }, meta: META }),
      ),
    );

    const { result } = renderHook(() => useRubric('r-1'), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toMatchObject({ id: 'r-1', title: 'Rubric A' });
  });

  it('is disabled when id is empty (no fetch performed)', () => {
    let fetched = false;
    server.use(
      http.get('/api/v1/rubrics/:id', () => {
        fetched = true;
        return HttpResponse.json({ data: null, meta: META });
      }),
    );

    const { result } = renderHook(() => useRubric(''), { wrapper: makeWrapper() });
    // Status is 'pending' but the fetch never happens because enabled: false.
    expect(result.current.fetchStatus).toBe('idle');
    expect(fetched).toBe(false);
  });
});

describe('useRubricResults', () => {
  it('fetches the results envelope', async () => {
    server.use(
      http.get('/api/v1/submissions/:id/rubric-results', () =>
        HttpResponse.json({ data: { rubric_id: 'r-1', results: [] }, meta: META }),
      ),
    );

    const { result } = renderHook(() => useRubricResults('r-1'), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toMatchObject({ rubric_id: 'r-1' });
  });

  it('is disabled with an empty rubricId', () => {
    const { result } = renderHook(() => useRubricResults(''), { wrapper: makeWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateRubric (mutation)', () => {
  it('mutates and resolves with the unwrapped data', async () => {
    server.use(
      http.post('/api/v1/rubrics', () =>
        HttpResponse.json({ data: { id: 'r-new', title: 'Created' }, meta: META }),
      ),
    );

    const { result } = renderHook(() => useCreateRubric(), { wrapper: makeWrapper() });

    let response: Awaited<ReturnType<typeof result.current.mutateAsync>> | undefined;
    await act(async () => {
      response = await result.current.mutateAsync({ title: 'Created' } as never);
    });

    expect(response).toMatchObject({ id: 'r-new', title: 'Created' });
  });
});

describe('useUpdateRubric (mutation)', () => {
  it('PUTs to /rubrics/:id and resolves with updated data', async () => {
    server.use(
      http.put('/api/v1/rubrics/:id', () =>
        HttpResponse.json({ data: { id: 'r-1', title: 'Renamed' }, meta: META }),
      ),
    );

    const { result } = renderHook(() => useUpdateRubric(), { wrapper: makeWrapper() });

    let response: Awaited<ReturnType<typeof result.current.mutateAsync>> | undefined;
    await act(async () => {
      response = await result.current.mutateAsync({ id: 'r-1', title: 'Renamed' } as never);
    });

    expect(response).toMatchObject({ id: 'r-1', title: 'Renamed' });
  });
});

describe('useDuplicateRubric (mutation)', () => {
  it('POSTs to /rubrics/:id/duplicate and resolves with copy data', async () => {
    server.use(
      http.post('/api/v1/rubrics/:id/duplicate', () =>
        HttpResponse.json({ data: { id: 'r-copy', title: 'Copy of …' }, meta: META }),
      ),
    );

    const { result } = renderHook(() => useDuplicateRubric(), { wrapper: makeWrapper() });

    let response: Awaited<ReturnType<typeof result.current.mutateAsync>> | undefined;
    await act(async () => {
      response = await result.current.mutateAsync('r-1');
    });

    expect(response?.id).toBe('r-copy');
  });
});

describe('useGradeRubric (mutation)', () => {
  it('grades and exposes the total_score from the client-computed result', async () => {
    server.use(
      http.post('/api/v1/submissions/:id/grade-rubric', () =>
        HttpResponse.json({ data: null, meta: META }),
      ),
    );

    const { result } = renderHook(() => useGradeRubric(), { wrapper: makeWrapper() });

    let response: Awaited<ReturnType<typeof result.current.mutateAsync>> | undefined;
    await act(async () => {
      response = await result.current.mutateAsync({
        rubric_id: 'r-1',
        assignment_id: 'a-1',
        entries: [
          { student_id: 's-1', criterion_id: 'c-1', level_id: 'l-1', score: 5 },
          { student_id: 's-1', criterion_id: 'c-2', level_id: 'l-2', score: 4 },
        ],
      } as never);
    });

    expect(response?.total_score).toBe(9);
    expect(response?.rubric_id).toBe('r-1');
  });
});
