/**
 * Tests for src/features/lms/student/model/useWriting.ts
 *
 * Covers `useSubmitWriting`:
 *   - Idle initial state
 *   - Successful submission with feedback
 *   - Error path (mutation surfaces the error)
 */
import { act, renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import type { ReactNode } from 'react';
import { describe, expect, it } from 'vitest';

import { server } from '../../../utils/mocks';

import { useSubmitWriting } from '@/features/lms/student/model/useWriting';

const META = { timestamp: '2026-06-01T00:00:00Z', version: '1.0.0' };

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe('useSubmitWriting', () => {
  it('starts in idle state', () => {
    const { result } = renderHook(() => useSubmitWriting(), { wrapper: makeWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('submits writing and exposes the feedback', async () => {
    server.use(
      http.post('/api/v1/writing-attempts', () =>
        HttpResponse.json({
          data: {
            id: 'a-1',
            text: 'Mon texte',
            feedback: {
              corrected_text: 'Mon texte (corrigé)',
              suggestions: ['Pense à la majuscule'],
              score: 8,
              encouragement: 'Bravo !',
            },
            created_at: '2026-06-01T10:00:00Z',
          },
          meta: META,
        }),
      ),
    );

    const { result } = renderHook(() => useSubmitWriting(), { wrapper: makeWrapper() });

    let response: Awaited<ReturnType<typeof result.current.mutateAsync>> | undefined;
    await act(async () => {
      response = await result.current.mutateAsync({ text: 'Mon texte', language: 'fr' });
    });

    expect(response?.feedback.score).toBe(8);
    expect(response?.feedback.suggestions).toContain('Pense à la majuscule');
    await waitFor(() => expect(result.current.status).toBe('success'));
  });

  it('surfaces an error when the API fails', async () => {
    server.use(
      http.post('/api/v1/writing-attempts', () =>
        HttpResponse.json({ error: { message: 'down' } }, { status: 503 }),
      ),
    );

    const { result } = renderHook(() => useSubmitWriting(), { wrapper: makeWrapper() });

    await act(async () => {
      try {
        await result.current.mutateAsync({ text: 'Boom' });
      } catch {
        // Expected; the mutation rejects on 5xx.
      }
    });

    await waitFor(() => expect(result.current.status).toBe('error'));
    expect(result.current.error).toBeDefined();
  });
});
