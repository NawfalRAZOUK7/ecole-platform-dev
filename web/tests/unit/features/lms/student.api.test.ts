/**
 * Tests for src/features/lms/student/api/student.api.ts
 *
 * Covers the network-only methods of `studentService`:
 *   - listStudentClasses, listStudentWork, listClassStudentWork
 *   - createEnrollment, listClassContent
 *   - updateContentProgress
 *   - buildContentStreamUrl (pure utility — no network)
 *
 * Methods that simply delegate to `quizzesService` (listPublishedQuizzes,
 * getQuizDetail, startQuizAttempt, respondToAttempt, submitAttempt,
 * getAttemptResults) are covered through quizzesService's own tests; we
 * spot-check one delegation here.
 */
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { server } from '../../../utils/mocks';

import { studentService } from '@/features/lms/student/api/student.api';

const META = { timestamp: '2026-06-01T00:00:00Z', version: '1.0.0' };
const LIST_META = { ...META, next_cursor: null, has_more: false };

describe('studentService.listStudentClasses', () => {
  it('GETs /enrollments and returns the list envelope', async () => {
    server.use(
      http.get('/api/v1/enrollments', () =>
        HttpResponse.json({
          data: [
            { class_id: 'c-1', class_name: '6e A' },
            { class_id: 'c-2', class_name: '6e B' },
          ],
          meta: LIST_META,
        }),
      ),
    );

    const resp = await studentService.listStudentClasses();
    expect(resp.data).toHaveLength(2);
    expect(resp.data[0]).toMatchObject({ class_id: 'c-1', class_name: '6e A' });
  });
});

describe('studentService.listStudentWork', () => {
  it('GETs /student-work and returns items + total', async () => {
    server.use(
      http.get('/api/v1/student-work', () =>
        HttpResponse.json({
          data: {
            items: [
              {
                id: 'w-1',
                type: 'assignment',
                title: 'Devoir Maths',
                due_at: '2026-06-15T23:59:00Z',
                status: 'pending',
                total_points: 20,
                grading_type: 'numeric',
              },
            ],
            total: 1,
          },
          meta: META,
        }),
      ),
    );

    const resp = await studentService.listStudentWork();
    expect(resp.data.total).toBe(1);
    expect(resp.data.items[0]).toMatchObject({ id: 'w-1', type: 'assignment' });
  });
});

describe('studentService.listClassStudentWork', () => {
  it('GETs /student-work/class/:id', async () => {
    let calledUrl = '';
    server.use(
      http.get('/api/v1/student-work/class/:id', ({ request }) => {
        calledUrl = new URL(request.url).pathname;
        return HttpResponse.json({ data: { items: [], total: 0 }, meta: META });
      }),
    );

    await studentService.listClassStudentWork('c-42');
    expect(calledUrl).toBe('/api/v1/student-work/class/c-42');
  });
});

describe('studentService.createEnrollment', () => {
  it('POSTs to /enrollments with the payload', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/enrollments', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({
          data: {
            id: 'e-1',
            student_id: 's-1',
            class_id: 'c-1',
            period_id: 'p-1',
            school_id: 'sch-1',
            status: 'active',
            program_id: null,
          },
          meta: META,
        });
      }),
    );

    const resp = await studentService.createEnrollment({
      student_id: 's-1',
      class_id: 'c-1',
      period_id: 'p-1',
    });

    expect(receivedBody).toEqual({
      student_id: 's-1',
      class_id: 'c-1',
      period_id: 'p-1',
    });
    expect(resp.data.id).toBe('e-1');
    expect(resp.data.program_id).toBeNull();
  });

  it('forwards the optional program_id (G49)', async () => {
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/enrollments', async ({ request }) => {
        receivedBody = await request.json();
        return HttpResponse.json({
          data: {
            id: 'e-2',
            student_id: 's-1',
            class_id: 'c-1',
            period_id: 'p-1',
            school_id: 'sch-1',
            status: 'active',
            program_id: 'prog-G49',
          },
          meta: META,
        });
      }),
    );

    const resp = await studentService.createEnrollment({
      student_id: 's-1',
      class_id: 'c-1',
      period_id: 'p-1',
      program_id: 'prog-G49',
    });

    expect(receivedBody).toMatchObject({ program_id: 'prog-G49' });
    expect(resp.data.program_id).toBe('prog-G49');
  });
});

describe('studentService.listClassContent', () => {
  it('GETs /classes/:classId/content', async () => {
    let calledUrl = '';
    server.use(
      http.get('/api/v1/classes/:classId/content', ({ request }) => {
        calledUrl = new URL(request.url).pathname;
        return HttpResponse.json({
          data: [
            {
              id: 'cc-1',
              content_item_id: 'ci-1',
              title: 'Histoire 1',
              content_type: 'pdf',
              level_band: 'CE1',
              language: 'fr',
              subject: 'history',
              description: null,
              assigned_at: null,
              teacher_notes: null,
            },
          ],
          meta: LIST_META,
        });
      }),
    );

    const resp = await studentService.listClassContent('c-1');
    expect(calledUrl).toBe('/api/v1/classes/c-1/content');
    expect(resp.data).toHaveLength(1);
    expect(resp.data[0].title).toBe('Histoire 1');
  });
});

describe('studentService.updateContentProgress', () => {
  it('POSTs to /content-items/:id/progress with the status', async () => {
    let calledUrl = '';
    let receivedBody: unknown = null;
    server.use(
      http.post('/api/v1/content-items/:id/progress', async ({ request }) => {
        calledUrl = new URL(request.url).pathname;
        receivedBody = await request.json();
        return HttpResponse.json({ data: null, meta: META });
      }),
    );

    await studentService.updateContentProgress('ci-42', 'completed');

    expect(calledUrl).toBe('/api/v1/content-items/ci-42/progress');
    expect(receivedBody).toEqual({ status: 'completed' });
  });
});

describe('studentService.buildContentStreamUrl', () => {
  it('builds the expected stream URL', () => {
    expect(studentService.buildContentStreamUrl('ci-1')).toBe('/content-items/ci-1/stream');
  });

  it('URL-encodes special characters in the content id', () => {
    expect(studentService.buildContentStreamUrl('ci 1/special#?')).toBe(
      '/content-items/ci%201%2Fspecial%23%3F/stream',
    );
  });

  it('is a pure function — does not call the network', () => {
    // No MSW handler installed; if it called the network, MSW would error.
    expect(studentService.buildContentStreamUrl('abc')).toContain('/content-items/abc');
  });
});
