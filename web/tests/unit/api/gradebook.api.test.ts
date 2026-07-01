/**
 * Tests for features/academic/gradebook/api/gradebook.api.ts
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { gradebookService } from '@/features/academic/gradebook/api/gradebook.api';

function mockFetch(data: unknown, status = 200) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: vi
      .fn()
      .mockResolvedValue(
        status >= 400
          ? {
              error: {
                code: 'ERR',
                message: String(data),
                category: 'system',
                retryable: false,
                timestamp: '',
              },
            }
          : { data, meta: { timestamp: '', version: '' } },
      ),
  });
}

beforeEach(() => {
  vi.stubGlobal('crypto', { randomUUID: () => 'test-uuid' });
  Object.defineProperty(document, 'cookie', { value: '', configurable: true, writable: true });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const mockBackendGradebook = {
  class_id: 'c1',
  class_name: 'Math',
  categories: [{ id: 'cat-1', name: 'Quiz', weight: 0.3 }],
  assignments: [
    { assignment_id: 'a1', title: 'Quiz 1', category_id: 'cat-1', total_points: 20, due_at: null },
  ],
  rows: [
    {
      student_id: 's1',
      student_name: 'Alice',
      assignments: [{ assignment_id: 'a1', score: 18 }],
      weighted_average: 18,
    },
  ],
};

describe('gradebookService', () => {
  it('getClassGradebook calls the gradebook endpoint and maps response', async () => {
    vi.stubGlobal('fetch', mockFetch(mockBackendGradebook));
    const result = await gradebookService.getClassGradebook('c1', 'p1');
    expect(result).toBeDefined();
    const url = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(url).toContain('gradebook');
    expect(url).toContain('c1');
  });

  it('getClassGradebook with programId includes program_id param', async () => {
    vi.stubGlobal('fetch', mockFetch(mockBackendGradebook));
    await gradebookService.getClassGradebook('c1', 'p1', 'prog-1');
    const url = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(url).toContain('program_id');
  });

  it('getStudentGrades calls the student grades endpoint', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch({
        student_id: 's1',
        student_name: 'Alice',
        academic_year: '2026',
        class: { id: 'c1', name: 'Math', code: 'M1' },
        periods: [],
      }),
    );
    const result = await gradebookService.getStudentGrades('s1');
    expect(result).toBeDefined();
  });

  it('getStudentGrades with academicYearId', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetch({
        student_id: 's1',
        student_name: 'Alice',
        academic_year: '2026',
        class: { id: 'c1', name: 'Math', code: 'M1' },
        periods: [],
      }),
    );
    await gradebookService.getStudentGrades('s1', 'year-1');
    const url = vi.mocked(fetch).mock.calls[0][0] as string;
    expect(url).toContain('s1');
  });

  it('updateGrades posts bulk grade update', async () => {
    vi.stubGlobal('fetch', mockFetch({ updated: 2 }));
    const result = await gradebookService.updateGrades({
      class_id: 'c1',
      period_id: 'p1',
      grades: [{ student_id: 's1', assignment_id: 'a1', score: 18 }],
    });
    expect(result.data).toBeDefined();
  });

  it('getWeightedSummary fetches summary', async () => {
    vi.stubGlobal('fetch', mockFetch(mockBackendGradebook));
    const result = await gradebookService.getWeightedSummary('c1', 'p1');
    expect(result.data).toBeDefined();
    expect(result.data.class_id).toBe('c1');
  });
});
