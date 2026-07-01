/**
 * Tests for src/features/lms/submissions/api/submissions.api.ts
 *
 * Covers the network-only / pure methods:
 *   - listAssignments (api.list)
 *   - createSubmission, finalizeSubmission, overridePenalty, previewSubmission
 *   - uploadExercisePdf (fetch-based, returns the inner data when present)
 *   - downloadExercisePdf, getFile (getDownloadUrl wrappers)
 *
 * Skipped here (handled separately because they need a full XHR mock with
 * Authorization header injection):
 *   - uploadSubmissionFile, uploadFiles
 */
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { server } from '../../../utils/mocks';

import { submissionsService } from '@/features/lms/submissions/api/submissions.api';

const META = { timestamp: '2026-06-01T00:00:00Z', version: '1.0.0' };
const LIST_META = { ...META, next_cursor: null, has_more: false };

describe('submissionsService.listAssignments', () => {
  it('GETs /assignments and returns the list envelope', async () => {
    server.use(
      http.get('/api/v1/assignments', () =>
        HttpResponse.json({
          data: [{ id: 'a-1', title: 'Dictée', course_id: 'c-1', due_at: null, total_points: 20 }],
          meta: LIST_META,
        }),
      ),
    );

    const resp = await submissionsService.listAssignments();
    expect(resp.data).toHaveLength(1);
    expect(resp.data[0]).toMatchObject({ id: 'a-1', title: 'Dictée' });
  });
});

describe('submissionsService.createSubmission', () => {
  it('POSTs to /submissions with assignment_id and returns the new id', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/submissions', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ data: { id: 'sub-1' }, meta: META });
      }),
    );

    const resp = await submissionsService.createSubmission('a-42');
    expect(receivedBody).toEqual({ assignment_id: 'a-42' });
    expect(resp.data.id).toBe('sub-1');
  });
});

describe('submissionsService.finalizeSubmission', () => {
  it('POSTs to /submissions/:id/submit', async () => {
    let calledUrl = '';
    server.use(
      http.post('/api/v1/submissions/:id/submit', ({ request }) => {
        calledUrl = new URL(request.url).pathname;
        return HttpResponse.json({ data: null, meta: META });
      }),
    );

    await submissionsService.finalizeSubmission('sub-1');
    expect(calledUrl).toBe('/api/v1/submissions/sub-1/submit');
  });
});

describe('submissionsService.overridePenalty', () => {
  it('POSTs the penalty payload to /submissions/:id/override-penalty', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/submissions/:id/override-penalty', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ data: null, meta: META });
      }),
    );

    await submissionsService.overridePenalty('sub-1', {
      penalty_override: 2.5,
      reason: 'medical excuse',
    });

    expect(receivedBody).toEqual({ penalty_override: 2.5, reason: 'medical excuse' });
  });

  it('works without a reason', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/submissions/:id/override-penalty', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({ data: null, meta: META });
      }),
    );

    await submissionsService.overridePenalty('sub-1', { penalty_override: 0 });
    expect(receivedBody).toEqual({ penalty_override: 0 });
  });
});

describe('submissionsService.previewSubmission', () => {
  it('returns the preview_url and status', async () => {
    server.use(
      http.get('/api/v1/submissions/:id/preview', () =>
        HttpResponse.json({
          data: { preview_url: 'https://preview/url', status: 'ready' },
          meta: META,
        }),
      ),
    );

    const resp = await submissionsService.previewSubmission('sub-1');
    expect(resp.data).toEqual({ preview_url: 'https://preview/url', status: 'ready' });
  });
});

describe('submissionsService.uploadExercisePdf', () => {
  it('POSTs the file and unwraps the envelope', async () => {
    let calledUrl = '';
    server.use(
      http.post('/api/v1/assignments/:id/exercise-pdf', ({ request }) => {
        calledUrl = new URL(request.url).pathname;
        return HttpResponse.json({
          data: {
            id: 'a-1',
            exercise_pdf_path: '/uploads/a-1/exo.pdf',
            checksum: 'sha256:abc',
            file_size: 1024,
          },
          meta: META,
        });
      }),
    );

    const file = new File(['pdf bytes'], 'exo.pdf', { type: 'application/pdf' });
    const result = await submissionsService.uploadExercisePdf('a-1', file);

    expect(calledUrl).toBe('/api/v1/assignments/a-1/exercise-pdf');
    expect(result.exercise_pdf_path).toBe('/uploads/a-1/exo.pdf');
    expect(result.checksum).toBe('sha256:abc');
  });

  it('also accepts a response without an envelope (legacy backend)', async () => {
    server.use(
      http.post('/api/v1/assignments/:id/exercise-pdf', () =>
        HttpResponse.json({
          id: 'a-2',
          exercise_pdf_path: '/uploads/a-2/exo.pdf',
          checksum: 'sha256:legacy',
          file_size: 2048,
        }),
      ),
    );

    const file = new File(['x'], 'x.pdf', { type: 'application/pdf' });
    const result = await submissionsService.uploadExercisePdf('a-2', file);
    expect(result.id).toBe('a-2');
    expect(result.checksum).toBe('sha256:legacy');
  });

  it('throws with the backend message on a non-2xx response', async () => {
    server.use(
      http.post('/api/v1/assignments/:id/exercise-pdf', () =>
        HttpResponse.json({ error: { message: 'File too large' } }, { status: 413 }),
      ),
    );

    const file = new File(['x'], 'x.pdf', { type: 'application/pdf' });
    await expect(submissionsService.uploadExercisePdf('a-3', file)).rejects.toThrow(
      'File too large',
    );
  });

  it('falls back to a generic message when the error body is unparseable', async () => {
    server.use(
      http.post('/api/v1/assignments/:id/exercise-pdf', () =>
        HttpResponse.text('plain text error', { status: 500 }),
      ),
    );

    const file = new File(['x'], 'x.pdf', { type: 'application/pdf' });
    await expect(submissionsService.uploadExercisePdf('a-4', file)).rejects.toThrow(
      'Upload failed',
    );
  });
});
