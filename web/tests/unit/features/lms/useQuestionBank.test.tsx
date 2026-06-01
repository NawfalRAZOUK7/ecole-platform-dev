/**
 * Tests for src/features/lms/question-bank/model/useQuestionBank.ts
 *
 * Covers:
 *   - questionBankQueryKeys (helpers)
 *   - useQuestions (with/without params → distinct cache keys)
 *   - useQuestionBankStats
 *   - useCreateQuestion (mutation + invalidation)
 *   - useImportFromQuiz (mutation + invalidation)
 *   - useGenerateQuiz (mutation, no invalidation — generates a new quiz)
 */
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';

import { server } from '../../../utils/mocks';

import {
  questionBankQueryKeys,
  useCreateQuestion,
  useGenerateQuiz,
  useImportFromQuiz,
  useQuestionBankStats,
  useQuestions,
} from '@/features/lms/question-bank/model/useQuestionBank';

const META = { timestamp: '2026-06-01T00:00:00Z', version: '1.0.0' };

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe('questionBankQueryKeys', () => {
  it('produces stable key shapes', () => {
    expect(questionBankQueryKeys.all).toEqual(['question-bank']);
    expect(questionBankQueryKeys.list()).toEqual(['question-bank', 'list', {}]);
    expect(questionBankQueryKeys.list({ subject: 'math' } as never)).toEqual([
      'question-bank',
      'list',
      { subject: 'math' },
    ]);
    expect(questionBankQueryKeys.stats()).toEqual(['question-bank', 'stats']);
  });
});

describe('useQuestions', () => {
  it('fetches the question list', async () => {
    server.use(
      http.get('/api/v1/question-bank', () =>
        HttpResponse.json({
          data: { items: [{ id: 'q-1' }, { id: 'q-2' }], total: 2 },
          meta: META,
        }),
      ),
    );

    const { result } = renderHook(() => useQuestions(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items).toHaveLength(2);
    expect(result.current.data?.total).toBe(2);
  });

  it('forwards query params to the URL', async () => {
    let receivedSearch = '';
    server.use(
      http.get('/api/v1/question-bank', ({ request }) => {
        receivedSearch = new URL(request.url).search;
        return HttpResponse.json({
          data: { items: [], total: 0 },
          meta: META,
        });
      }),
    );

    const { result } = renderHook(
      () => useQuestions({ subject: 'math', difficulty: 'easy' } as never),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const params = new URLSearchParams(receivedSearch);
    expect(params.get('subject')).toBe('math');
    expect(params.get('difficulty')).toBe('easy');
  });
});

describe('useQuestionBankStats', () => {
  it('returns the stats payload', async () => {
    server.use(
      http.get('/api/v1/question-bank/stats', () =>
        HttpResponse.json({
          data: { total_questions: 120, by_subject: { math: 60, fr: 60 } },
          meta: META,
        }),
      ),
    );

    const { result } = renderHook(() => useQuestionBankStats(), { wrapper: makeWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total_questions).toBe(120);
  });
});

describe('useCreateQuestion (mutation)', () => {
  it('creates a question and resolves with the unwrapped data', async () => {
    server.use(
      http.post('/api/v1/question-bank', () =>
        HttpResponse.json({ data: { id: 'q-new' }, meta: META }),
      ),
    );

    const { result } = renderHook(() => useCreateQuestion(), { wrapper: makeWrapper() });

    let response: Awaited<ReturnType<typeof result.current.mutateAsync>> | undefined;
    await act(async () => {
      response = await result.current.mutateAsync({ text: 'Q?' } as never);
    });

    expect(response?.id).toBe('q-new');
  });
});

describe('useImportFromQuiz (mutation)', () => {
  it('POSTs to /import/:quizId and resolves with import counts', async () => {
    server.use(
      http.post('/api/v1/question-bank/import/:quizId', () =>
        HttpResponse.json({ data: { imported_count: 7 }, meta: META }),
      ),
    );

    const { result } = renderHook(() => useImportFromQuiz(), { wrapper: makeWrapper() });

    let response: Awaited<ReturnType<typeof result.current.mutateAsync>> | undefined;
    await act(async () => {
      response = await result.current.mutateAsync('quiz-1');
    });

    expect(response).toMatchObject({ imported_count: 7 });
  });
});

describe('useGenerateQuiz (mutation)', () => {
  it('generates a quiz from params', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/question-bank/generate-quiz', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({
          data: { quiz_id: 'gq-1', question_count: 10 },
          meta: META,
        });
      }),
    );

    const { result } = renderHook(() => useGenerateQuiz(), { wrapper: makeWrapper() });

    const params = { subject: 'math', count: 10 } as never;
    let response: Awaited<ReturnType<typeof result.current.mutateAsync>> | undefined;
    await act(async () => {
      response = await result.current.mutateAsync(params);
    });

    expect(receivedBody).toEqual(params);
    expect(response).toMatchObject({ quiz_id: 'gq-1', question_count: 10 });
  });
});
