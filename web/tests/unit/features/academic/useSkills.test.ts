import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useSkillDimensions,
  useSkillMilestones,
  useStudentSkillProgress,
  useSkillPassport,
  useClassSkillAnalytics,
  useSchoolSkillAnalytics,
  useSkillLeaderboard,
  useCreateSkillDimension,
  useCreateSkillMilestone,
  useEvaluateStudentSkills,
  useGenerateSkillPassport,
  useDownloadSkillPassport,
  skillsQueryKeys,
} from '@/features/academic/skills/model/useSkills';

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

describe('skillsQueryKeys', () => {
  it('generates correct query keys', () => {
    expect(skillsQueryKeys.all).toEqual(['skills']);
    expect(skillsQueryKeys.dimensions()).toEqual(['skills', 'dimensions']);
    expect(skillsQueryKeys.milestones()).toEqual(['skills', 'milestones', 'all']);
    expect(skillsQueryKeys.milestones('dim1')).toEqual(['skills', 'milestones', 'dim1']);
    expect(skillsQueryKeys.progress('s1', 'ay1')).toEqual(['skills', 'progress', 's1', 'ay1']);
    expect(skillsQueryKeys.passport('s1', 'ay1')).toEqual(['skills', 'passport', 's1', 'ay1']);
    expect(skillsQueryKeys.classAnalytics('c1', 'ay1')).toEqual([
      'skills',
      'class-analytics',
      'c1',
      'ay1',
    ]);
    expect(skillsQueryKeys.schoolAnalytics('ay1')).toEqual(['skills', 'school-analytics', 'ay1']);
    expect(skillsQueryKeys.leaderboard('c1', 'ay1', 10)).toEqual([
      'skills',
      'leaderboard',
      'c1',
      'ay1',
      10,
    ]);
  });
});

describe('useSkillDimensions', () => {
  it('fetches dimensions successfully', async () => {
    server.use(
      http.get('/api/v1/skills/dimensions', () =>
        apiListResponse([
          {
            id: 'dim1',
            name: 'Social',
            description: null,
            is_active: true,
            created_at: '2026-01-01',
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useSkillDimensions(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data![0].id).toBe('dim1');
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/skills/dimensions', () => apiErrorResponse()));
    const { result } = renderHook(() => useSkillDimensions(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useSkillMilestones', () => {
  it('fetches milestones without filter', async () => {
    server.use(
      http.get('/api/v1/skills/milestones', () =>
        apiListResponse([
          {
            id: 'm1',
            dimension_id: 'dim1',
            name: 'Level 1',
            description: null,
            order: 1,
            is_active: true,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useSkillMilestones(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].id).toBe('m1');
  });

  it('fetches milestones with dimensionId filter', async () => {
    server.use(
      http.get('/api/v1/skills/milestones', () =>
        apiListResponse([
          {
            id: 'm2',
            dimension_id: 'dim1',
            name: 'Level 2',
            description: null,
            order: 2,
            is_active: true,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useSkillMilestones('dim1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].dimension_id).toBe('dim1');
  });
});

describe('useStudentSkillProgress', () => {
  it('fetches progress when both ids provided', async () => {
    server.use(
      http.get('/api/v1/skills/progress/student/:studentId', () =>
        apiListResponse([
          {
            id: 'prog1',
            student_id: 's1',
            milestone_id: 'm1',
            status: 'achieved',
            evaluated_at: '2026-01-01',
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useStudentSkillProgress('s1', 'ay1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
  });

  it('does not fetch when studentId is empty', () => {
    const { result } = renderHook(() => useStudentSkillProgress('', 'ay1'), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('does not fetch when academicYearId is empty', () => {
    const { result } = renderHook(() => useStudentSkillProgress('s1', ''), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useSkillPassport', () => {
  it('fetches passport', async () => {
    server.use(
      http.get('/api/v1/skills/passport/:studentId', () =>
        apiResponse({
          student_id: 's1',
          academic_year_id: 'ay1',
          dimensions: [],
          generated_at: '2026-01-01',
        }),
      ),
    );
    const { result } = renderHook(() => useSkillPassport('s1', 'ay1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.student_id).toBe('s1');
  });

  it('does not fetch when ids missing', () => {
    const { result } = renderHook(() => useSkillPassport('', 'ay1'), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useClassSkillAnalytics', () => {
  it('fetches class analytics', async () => {
    server.use(
      http.get('/api/v1/skills/analytics/class/:classId', () =>
        apiResponse({ class_id: 'c1', academic_year_id: 'ay1', dimensions: [], student_count: 20 }),
      ),
    );
    const { result } = renderHook(() => useClassSkillAnalytics('c1', 'ay1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.class_id).toBe('c1');
  });

  it('is idle with empty classId', () => {
    const { result } = renderHook(() => useClassSkillAnalytics('', 'ay1'), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useSchoolSkillAnalytics', () => {
  it('fetches school analytics', async () => {
    server.use(
      http.get('/api/v1/skills/analytics/school', () =>
        apiResponse({ academic_year_id: 'ay1', dimensions: [], student_count: 100 }),
      ),
    );
    const { result } = renderHook(() => useSchoolSkillAnalytics('ay1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('is idle with empty academicYearId', () => {
    const { result } = renderHook(() => useSchoolSkillAnalytics(''), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useSkillLeaderboard', () => {
  it('fetches leaderboard', async () => {
    server.use(
      http.get('/api/v1/skills/leaderboard/:classId', () =>
        apiListResponse([{ student_id: 's1', student_name: 'Alice', score: 95, rank: 1 }]),
      ),
    );
    const { result } = renderHook(() => useSkillLeaderboard('c1', 'ay1', 10), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].rank).toBe(1);
  });

  it('is idle with empty classId', () => {
    const { result } = renderHook(() => useSkillLeaderboard('', 'ay1', 10), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateSkillDimension', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateSkillDimension(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('creates a dimension', async () => {
    server.use(
      http.post('/api/v1/skills/dimensions', () =>
        apiResponse({
          id: 'dim2',
          name: 'Cognitive',
          description: null,
          is_active: true,
          created_at: '2026-01-01',
        }),
      ),
      http.get('/api/v1/skills/dimensions', () => apiListResponse([])),
    );
    const { result } = renderHook(() => useCreateSkillDimension(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync({ name: 'Cognitive', description: null });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useCreateSkillMilestone', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateSkillMilestone(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useEvaluateStudentSkills', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useEvaluateStudentSkills(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('evaluates student skills', async () => {
    server.use(
      http.post('/api/v1/skills/evaluate/:studentId', () =>
        apiResponse({
          student_id: 's1',
          academic_year_id: 'ay1',
          evaluated_at: '2026-01-01',
          scores: [],
        }),
      ),
      http.get('/api/v1/skills/progress/student/:studentId', () => apiListResponse([])),
      http.get('/api/v1/skills/passport/:studentId', () =>
        apiResponse({
          student_id: 's1',
          academic_year_id: 'ay1',
          dimensions: [],
          generated_at: null,
        }),
      ),
      http.get('/api/v1/skills/dimensions', () => apiListResponse([])),
    );
    const { result } = renderHook(() => useEvaluateStudentSkills(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync({ studentId: 's1', academicYearId: 'ay1' });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useGenerateSkillPassport', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useGenerateSkillPassport(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useDownloadSkillPassport', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useDownloadSkillPassport(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});
