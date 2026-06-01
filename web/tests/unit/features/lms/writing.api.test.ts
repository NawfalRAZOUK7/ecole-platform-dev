/**
 * Tests for src/features/lms/student/api/writing.api.ts
 *
 * Covers `writingService.submitWriting`:
 *   - POSTs to /writing-attempts
 *   - Unwraps the envelope (returns resp.data directly, not the envelope)
 *   - Forwards the request body verbatim
 *   - Propagates HTTP errors
 */
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { server } from '../../../utils/mocks';

import { writingService } from '@/features/lms/student/api/writing.api';

const META = { timestamp: '2026-06-01T00:00:00Z', version: '1.0.0' };

describe('writingService.submitWriting', () => {
  it('POSTs the body to /writing-attempts and returns the unwrapped data', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/writing-attempts', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({
          data: {
            id: 'attempt-1',
            text: 'Mon texte',
            feedback: {
              corrected_text: 'Mon texte (corrigé)',
              suggestions: ['Bien essayé'],
              score: 8,
              encouragement: 'Continue !',
            },
            created_at: '2026-06-01T10:00:00Z',
          },
          meta: META,
        });
      }),
    );

    const result = await writingService.submitWriting({
      text: 'Mon texte',
      language: 'fr',
      writing_type: 'narration',
    });

    expect(receivedBody).toEqual({
      text: 'Mon texte',
      language: 'fr',
      writing_type: 'narration',
    });

    // submitWriting unwraps the envelope (return resp.data)
    expect(result.id).toBe('attempt-1');
    expect(result.feedback.score).toBe(8);
    expect(result.feedback.suggestions).toContain('Bien essayé');
  });

  it('works with only the required text field', async () => {
    server.use(
      http.post('/api/v1/writing-attempts', () =>
        HttpResponse.json({
          data: {
            id: 'a-2',
            text: 'Hello',
            feedback: {
              corrected_text: 'Hello',
              suggestions: [],
              score: null,
              encouragement: '',
            },
            created_at: '2026-06-01T10:00:00Z',
          },
          meta: META,
        }),
      ),
    );

    const result = await writingService.submitWriting({ text: 'Hello' });

    expect(result.id).toBe('a-2');
    expect(result.feedback.score).toBeNull();
  });

  it('propagates HTTP errors', async () => {
    server.use(
      http.post('/api/v1/writing-attempts', () =>
        HttpResponse.json({ error: { message: 'Internal' } }, { status: 500 }),
      ),
    );

    await expect(writingService.submitWriting({ text: 'Boom' })).rejects.toBeDefined();
  });
});
