/**
 * Tests for src/features/lms/question-bank/api/question-bank.api.ts
 *
 * Covers every method of `questionBankService`:
 *   - createQuestion, listQuestions (with URL query building), importFromQuiz,
 *     generateQuiz, getStats
 *
 * Particular attention to listQuestions: it builds a URLSearchParams from
 * 5 optional fields. We verify every combination of present/absent params.
 */
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { server } from '../../../utils/mocks';

import { questionBankService } from '@/features/lms/question-bank/api/question-bank.api';

const META = { timestamp: '2026-06-01T00:00:00Z', version: '1.0.0' };

describe('questionBankService.createQuestion', () => {
  it('POSTs to /question-bank with the payload', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/question-bank', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ data: { id: 'q-new' }, meta: META });
      }),
    );

    const payload = { text: 'Q1?', type: 'mcq' } as never;
    const resp = await questionBankService.createQuestion(payload);

    expect(receivedBody).toEqual(payload);
    expect(resp.data.id).toBe('q-new');
  });
});

describe('questionBankService.listQuestions', () => {
  it('lists with NO query params when called without arguments', async () => {
    let calledUrl = '';
    server.use(
      http.get('/api/v1/question-bank', ({ request }) => {
        calledUrl = request.url;
        return HttpResponse.json({ data: { items: [], total: 0 }, meta: META });
      }),
    );

    await questionBankService.listQuestions();
    expect(new URL(calledUrl).search).toBe('');
  });

  it('builds query string with subject + type + difficulty', async () => {
    let search = '';
    server.use(
      http.get('/api/v1/question-bank', ({ request }) => {
        search = new URL(request.url).search;
        return HttpResponse.json({ data: { items: [], total: 0 }, meta: META });
      }),
    );

    await questionBankService.listQuestions({
      subject: 'math',
      type: 'mcq',
      difficulty: 'easy',
    } as never);

    const params = new URLSearchParams(search);
    expect(params.get('subject')).toBe('math');
    expect(params.get('type')).toBe('mcq');
    expect(params.get('difficulty')).toBe('easy');
  });

  it('includes page and page_size when explicitly set, including zero', async () => {
    let search = '';
    server.use(
      http.get('/api/v1/question-bank', ({ request }) => {
        search = new URL(request.url).search;
        return HttpResponse.json({ data: { items: [], total: 0 }, meta: META });
      }),
    );

    await questionBankService.listQuestions({ page: 0, page_size: 50 } as never);

    const params = new URLSearchParams(search);
    expect(params.get('page')).toBe('0');
    expect(params.get('page_size')).toBe('50');
  });

  it('omits keys whose value is undefined or null', async () => {
    let search = '';
    server.use(
      http.get('/api/v1/question-bank', ({ request }) => {
        search = new URL(request.url).search;
        return HttpResponse.json({ data: { items: [], total: 0 }, meta: META });
      }),
    );

    await questionBankService.listQuestions({
      subject: 'math',
      type: undefined,
      difficulty: undefined,
      page: undefined,
      page_size: undefined,
    } as never);

    const params = new URLSearchParams(search);
    expect(params.get('subject')).toBe('math');
    expect(params.has('type')).toBe(false);
    expect(params.has('page')).toBe(false);
  });

  it('returns the list payload through the envelope', async () => {
    server.use(
      http.get('/api/v1/question-bank', () =>
        HttpResponse.json({
          data: { items: [{ id: 'q-1' }, { id: 'q-2' }], total: 2 },
          meta: META,
        }),
      ),
    );

    const resp = await questionBankService.listQuestions();
    expect(resp.data.items).toHaveLength(2);
    expect(resp.data.total).toBe(2);
  });
});

describe('questionBankService.importFromQuiz', () => {
  it('POSTs to /question-bank/import/:quizId with an empty body', async () => {
    let receivedBody: unknown = null;
    let calledUrl = '';
    server.use(
      http.post('/api/v1/question-bank/import/:quizId', async ({ request }) => {
        calledUrl = new URL(request.url).pathname;
        receivedBody = await request.json();
        return HttpResponse.json({
          data: { imported_count: 12 },
          meta: META,
        });
      }),
    );

    const resp = await questionBankService.importFromQuiz('quiz-42');

    expect(calledUrl).toBe('/api/v1/question-bank/import/quiz-42');
    expect(receivedBody).toEqual({});
    expect(resp.data).toMatchObject({ imported_count: 12 });
  });
});

describe('questionBankService.generateQuiz', () => {
  it('POSTs to /question-bank/generate-quiz with params', async () => {
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

    const params = { subject: 'math', count: 10, difficulty: 'medium' } as never;
    const resp = await questionBankService.generateQuiz(params);

    expect(receivedBody).toEqual(params);
    expect(resp.data).toMatchObject({ quiz_id: 'gq-1', question_count: 10 });
  });
});

describe('questionBankService.getStats', () => {
  it('GETs /question-bank/stats', async () => {
    server.use(
      http.get('/api/v1/question-bank/stats', () =>
        HttpResponse.json({
          data: { total_questions: 250, by_subject: { math: 120, fr: 80 } },
          meta: META,
        }),
      ),
    );

    const resp = await questionBankService.getStats();
    expect(resp.data.total_questions).toBe(250);
  });
});
