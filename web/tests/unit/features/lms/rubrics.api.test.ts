/**
 * Tests for src/features/lms/rubrics/api/rubrics.api.ts
 *
 * Covers every method of `rubricsService`:
 *   - listRubrics, getRubric, createRubric, updateRubric, duplicateRubric
 *   - gradeRubric (also computes totalScore client-side)
 *   - getRubricResults
 *
 * Convention: api.get/post/put/delete return ApiResponse<T> = { data: T, meta }.
 */
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { server } from '../../../utils/mocks';

import { rubricsService } from '@/features/lms/rubrics/api/rubrics.api';

const META = { timestamp: '2026-06-01T00:00:00Z', version: '1.0.0' };
const LIST_META = { ...META, next_cursor: null, has_more: false };

describe('rubricsService.listRubrics', () => {
  it('returns the list payload', async () => {
    server.use(
      http.get('/api/v1/rubrics', () =>
        HttpResponse.json({ data: [{ id: 'r-1', title: 'Math rubric' }], meta: LIST_META }),
      ),
    );

    const resp = await rubricsService.listRubrics();
    // api.get returns the envelope, caller reads .data
    expect(resp.data).toHaveLength(1);
    expect(resp.data[0]).toMatchObject({ id: 'r-1', title: 'Math rubric' });
  });

  it('returns empty array for no rubrics', async () => {
    server.use(http.get('/api/v1/rubrics', () => HttpResponse.json({ data: [], meta: LIST_META })));

    const resp = await rubricsService.listRubrics();
    expect(resp.data).toEqual([]);
  });
});

describe('rubricsService.getRubric', () => {
  it('calls /rubrics/:id and returns the rubric', async () => {
    let calledUrl = '';
    server.use(
      http.get('/api/v1/rubrics/:id', ({ request, params }) => {
        calledUrl = new URL(request.url).pathname;
        return HttpResponse.json({
          data: { id: params.id, title: 'Specific rubric' },
          meta: META,
        });
      }),
    );

    const resp = await rubricsService.getRubric('r-42');
    expect(calledUrl).toBe('/api/v1/rubrics/r-42');
    expect(resp.data).toMatchObject({ id: 'r-42', title: 'Specific rubric' });
  });
});

describe('rubricsService.createRubric', () => {
  it('POSTs to /rubrics with the payload', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/rubrics', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({
          data: { id: 'r-new', title: 'Created rubric' },
          meta: META,
        });
      }),
    );

    const payload = { title: 'New', criteria: [] } as never;
    const resp = await rubricsService.createRubric(payload);

    expect(receivedBody).toEqual(payload);
    expect(resp.data).toMatchObject({ id: 'r-new' });
  });
});

describe('rubricsService.updateRubric', () => {
  it('PUTs to /rubrics/:id with the payload', async () => {
    let method = '';
    let receivedBody: unknown = null;
    server.use(
      http.put('/api/v1/rubrics/:id', async ({ request }) => {
        method = request.method;
        receivedBody = await request.json();
        return HttpResponse.json({
          data: { id: 'r-1', title: 'Updated' },
          meta: META,
        });
      }),
    );

    const resp = await rubricsService.updateRubric('r-1', { title: 'Updated' } as never);

    expect(method).toBe('PUT');
    expect(receivedBody).toEqual({ title: 'Updated' });
    expect(resp.data).toMatchObject({ id: 'r-1', title: 'Updated' });
  });
});

describe('rubricsService.duplicateRubric', () => {
  it('POSTs to /rubrics/:id/duplicate with an empty body', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/rubrics/:id/duplicate', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({
          data: { id: 'r-copy', title: 'Copy of …' },
          meta: META,
        });
      }),
    );

    const resp = await rubricsService.duplicateRubric('r-1');

    expect(receivedBody).toEqual({});
    expect(resp.data.id).toBe('r-copy');
  });
});

describe('rubricsService.gradeRubric', () => {
  it('POSTs entries and computes total_score client-side', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/submissions/:id/grade-rubric', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ data: null, meta: META });
      }),
    );

    const result = await rubricsService.gradeRubric({
      rubric_id: 'r-1',
      assignment_id: 'a-1',
      entries: [
        { student_id: 's-1', criterion_id: 'c-1', level_id: 'l-1', score: 4 },
        { student_id: 's-1', criterion_id: 'c-2', level_id: 'l-2', score: 3 },
      ],
    } as never);

    expect(receivedBody).toEqual([
      { criterion_id: 'c-1', level_id: 'l-1', points_awarded: 4, comment: null },
      { criterion_id: 'c-2', level_id: 'l-2', points_awarded: 3, comment: null },
    ]);
    expect(result.data.total_score).toBe(7);
    expect(result.data.max_score).toBe(7);
    expect(result.data.percentage).toBe(100);
    expect(result.data.rubric_id).toBe('r-1');
    expect(result.data.student_id).toBe('s-1');
  });

  it('falls back to rubric_id when assignment_id is omitted', async () => {
    let calledUrl = '';
    server.use(
      http.post('/api/v1/submissions/:id/grade-rubric', ({ request }) => {
        calledUrl = new URL(request.url).pathname;
        return HttpResponse.json({ data: null, meta: META });
      }),
    );

    await rubricsService.gradeRubric({
      rubric_id: 'r-only',
      entries: [{ student_id: 's-1', criterion_id: 'c-1', level_id: 'l-1', score: 5 }],
    } as never);

    expect(calledUrl).toBe('/api/v1/submissions/r-only/grade-rubric');
  });

  it('handles an empty entries array', async () => {
    server.use(
      http.post('/api/v1/submissions/:id/grade-rubric', () =>
        HttpResponse.json({ data: null, meta: META }),
      ),
    );

    const result = await rubricsService.gradeRubric({
      rubric_id: 'r-1',
      assignment_id: 'a-1',
      entries: [],
    } as never);

    expect(result.data.total_score).toBe(0);
    expect(result.data.student_id).toBe('');
  });
});

describe('rubricsService.getRubricResults', () => {
  it('calls /submissions/:rubricId/rubric-results', async () => {
    let calledUrl = '';
    server.use(
      http.get('/api/v1/submissions/:id/rubric-results', ({ request }) => {
        calledUrl = new URL(request.url).pathname;
        return HttpResponse.json({
          data: { rubric_id: 'r-1', results: [] },
          meta: META,
        });
      }),
    );

    const resp = await rubricsService.getRubricResults('r-1');
    expect(calledUrl).toBe('/api/v1/submissions/r-1/rubric-results');
    expect(resp.data).toMatchObject({ rubric_id: 'r-1' });
  });
});
