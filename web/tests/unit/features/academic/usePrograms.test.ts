import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useProgramsQuery,
  useProgramQuery,
  useCreateProgramMutation,
  useUpdateProgramMutation,
  useAssignProgramMutation,
  useStudentProgramHistoryQuery,
  useStudentAcademicTimelineQuery,
  useStudentCurrentProgramQuery,
  useProgramVersionsQuery,
  useCreateProgramVersionMutation,
  useUpdateProgramVersionMutation,
  useProgramEquivalencesQuery,
  useCreateEquivalenceMutation,
  useDeleteEquivalenceMutation,
  useStudentSnapshotsQuery,
  useTakeSnapshotMutation,
  useSnapshotTranscriptMutation,
  useEligibilityRulesQuery,
  useCreateEligibilityRuleMutation,
  useDeleteEligibilityRuleMutation,
  useEligibilityCheckQuery,
  programQueryKeys,
} from '@/features/academic/programs/model/usePrograms';

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

const mockProgram = {
  id: 'prog1',
  school_id: 's1',
  code: 'CE2',
  name: 'CE2 Program',
  level: 'primary',
  description: null,
  is_active: true,
  version_label: 'v1',
  effective_from: null,
  created_at: '2026-01-01',
  updated_at: null,
};

describe('programQueryKeys', () => {
  it('generates correct keys', () => {
    expect(programQueryKeys.all).toEqual(['programs']);
    expect(programQueryKeys.list(true)).toEqual(['programs', 'list', true]);
    expect(programQueryKeys.byId('p1')).toEqual(['programs', 'detail', 'p1']);
    expect(programQueryKeys.studentHistory('s1')).toEqual(['programs', 'student-history', 's1']);
    expect(programQueryKeys.studentTimeline('s1')).toEqual(['programs', 'student-timeline', 's1']);
    expect(programQueryKeys.studentCurrent('s1')).toEqual(['programs', 'student-current', 's1']);
  });
});

describe('useProgramsQuery', () => {
  it('fetches programs', async () => {
    server.use(http.get('/api/v1/programs', () => apiListResponse([mockProgram])));
    const { result } = renderHook(() => useProgramsQuery(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data![0].id).toBe('prog1');
  });

  it('is idle when disabled', () => {
    const { result } = renderHook(() => useProgramsQuery(true, false), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/programs', () => apiErrorResponse()));
    const { result } = renderHook(() => useProgramsQuery(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useProgramQuery', () => {
  it('fetches a single program by id', async () => {
    server.use(http.get('/api/v1/programs/:id', () => apiResponse(mockProgram)));
    const { result } = renderHook(() => useProgramQuery('prog1'), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.code).toBe('CE2');
  });

  it('is idle when programId is undefined', () => {
    const { result } = renderHook(() => useProgramQuery(undefined), { wrapper: createWrapper() });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateProgramMutation', () => {
  it('creates a program', async () => {
    server.use(
      http.post('/api/v1/programs', () => apiResponse(mockProgram)),
      http.get('/api/v1/programs', () => apiListResponse([mockProgram])),
    );
    const { result } = renderHook(() => useCreateProgramMutation(), { wrapper: createWrapper() });
    await act(async () => {
      const data = await result.current.mutateAsync({ code: 'CE2', name: 'CE2 Program' });
      expect(data.id).toBe('prog1');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useUpdateProgramMutation', () => {
  it('updates a program', async () => {
    const updated = { ...mockProgram, name: 'Updated Program' };
    server.use(
      http.patch('/api/v1/programs/:id', () => apiResponse(updated)),
      http.get('/api/v1/programs', () => apiListResponse([updated])),
    );
    const { result } = renderHook(() => useUpdateProgramMutation(), { wrapper: createWrapper() });
    await act(async () => {
      const data = await result.current.mutateAsync({
        programId: 'prog1',
        body: { name: 'Updated Program' },
      });
      expect(data.name).toBe('Updated Program');
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useAssignProgramMutation', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useAssignProgramMutation(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });

  it('assigns a program and invalidates related caches', async () => {
    server.use(
      http.post('/api/v1/enrollments/:id/program', () =>
        apiResponse({
          id: 'event1',
          school_id: 's1',
          student_id: 'stu1',
          academic_year_id: 'ay1',
          period_id: null,
          from_program_id: null,
          to_program_id: 'prog1',
          from_enrollment_id: null,
          to_enrollment_id: 'enr1',
          reason_code: 'INITIAL',
          reason_note: null,
          actor_user_id: null,
          occurred_at: '2026-01-01',
        }),
      ),
      http.get('/api/v1/students/:id/program-history', () => apiListResponse([])),
      http.get('/api/v1/students/:id/academic-timeline', () => apiListResponse([])),
      http.get('/api/v1/students/:id/current-program', () =>
        apiResponse({
          student_id: 'stu1',
          academic_year_id: 'ay1',
          period_id: null,
          enrollment_id: null,
          program: null,
        }),
      ),
    );
    const { result } = renderHook(() => useAssignProgramMutation(), { wrapper: createWrapper() });
    await act(async () => {
      await result.current.mutateAsync({
        enrollmentId: 'enr1',
        body: { program_id: 'prog1', reason_code: 'INITIAL' },
        studentId: 'stu1',
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });
});

describe('useStudentProgramHistoryQuery', () => {
  it('fetches student program history', async () => {
    server.use(
      http.get('/api/v1/students/:studentId/program-history', () =>
        apiListResponse([{ id: 'ev1' }]),
      ),
    );
    const { result } = renderHook(() => useStudentProgramHistoryQuery('stu1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(1);
  });

  it('is idle when studentId is undefined', () => {
    const { result } = renderHook(() => useStudentProgramHistoryQuery(undefined), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useStudentAcademicTimelineQuery', () => {
  it('fetches academic timeline', async () => {
    server.use(
      http.get('/api/v1/students/:studentId/academic-timeline', () => apiListResponse([])),
    );
    const { result } = renderHook(() => useStudentAcademicTimelineQuery('stu1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('is idle when studentId is undefined', () => {
    const { result } = renderHook(() => useStudentAcademicTimelineQuery(undefined), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useStudentCurrentProgramQuery', () => {
  it('fetches current program', async () => {
    server.use(
      http.get('/api/v1/students/:studentId/current-program', () =>
        apiResponse({
          student_id: 'stu1',
          academic_year_id: 'ay1',
          period_id: null,
          enrollment_id: 'enr1',
          program: null,
        }),
      ),
    );
    const { result } = renderHook(() => useStudentCurrentProgramQuery('stu1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.student_id).toBe('stu1');
  });
});

describe('useProgramVersionsQuery', () => {
  it('fetches versions for a program', async () => {
    server.use(
      http.get('/api/v1/programs/:id/versions', () =>
        apiListResponse([
          {
            id: 'v1',
            school_id: 's1',
            program_id: 'prog1',
            version_label: 'v1.0',
            description: null,
            effective_from: null,
            retired_at: null,
            is_active: true,
            created_at: '2026-01-01',
            updated_at: null,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useProgramVersionsQuery('prog1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].version_label).toBe('v1.0');
  });

  it('is idle when programId is undefined', () => {
    const { result } = renderHook(() => useProgramVersionsQuery(undefined), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useCreateProgramVersionMutation', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateProgramVersionMutation(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });
});

describe('useUpdateProgramVersionMutation', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useUpdateProgramVersionMutation(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });
});

describe('useProgramEquivalencesQuery', () => {
  it('fetches equivalences', async () => {
    server.use(
      http.get('/api/v1/program-equivalences', () =>
        apiListResponse([
          {
            id: 'eq1',
            school_id: 's1',
            from_program_id: 'p1',
            to_program_id: 'p2',
            kind: 'EQUIVALENT',
            note: null,
            ratified_at: null,
            ratified_by: null,
            created_at: '2026-01-01',
            updated_at: null,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useProgramEquivalencesQuery(), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].id).toBe('eq1');
  });
});

describe('useCreateEquivalenceMutation', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateEquivalenceMutation(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });
});

describe('useDeleteEquivalenceMutation', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useDeleteEquivalenceMutation(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });
});

describe('useStudentSnapshotsQuery', () => {
  it('fetches snapshots', async () => {
    server.use(
      http.get('/api/v1/students/:studentId/snapshots', () =>
        apiListResponse([
          {
            id: 'snap1',
            school_id: 's1',
            student_id: 'stu1',
            academic_year_id: 'ay1',
            snapshot_kind: 'YEAR_END',
            snapshot_data: {},
            taken_at: '2026-06-01',
            taken_by: null,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useStudentSnapshotsQuery('stu1'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].id).toBe('snap1');
  });

  it('is idle when studentId is undefined', () => {
    const { result } = renderHook(() => useStudentSnapshotsQuery(undefined), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useTakeSnapshotMutation', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useTakeSnapshotMutation(), { wrapper: createWrapper() });
    expect(result.current.status).toBe('idle');
  });
});

describe('useSnapshotTranscriptMutation', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useSnapshotTranscriptMutation(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });
});

describe('useEligibilityRulesQuery', () => {
  it('fetches eligibility rules', async () => {
    server.use(
      http.get('/api/v1/eligibility/rules', () =>
        apiListResponse([
          {
            id: 'rule1',
            school_id: 's1',
            kind: 'PROMOTION',
            target_program_id: 'p1',
            condition_type: 'gpa_minimum',
            condition_params: {},
            message_key: 'min_gpa',
            is_active: true,
          },
        ]),
      ),
    );
    const { result } = renderHook(() => useEligibilityRulesQuery(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data![0].id).toBe('rule1');
  });
});

describe('useCreateEligibilityRuleMutation', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useCreateEligibilityRuleMutation(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });
});

describe('useDeleteEligibilityRuleMutation', () => {
  it('is idle initially', () => {
    const { result } = renderHook(() => useDeleteEligibilityRuleMutation(), {
      wrapper: createWrapper(),
    });
    expect(result.current.status).toBe('idle');
  });
});

describe('useEligibilityCheckQuery', () => {
  it('fetches eligibility when both ids provided', async () => {
    server.use(
      http.get('/api/v1/students/:studentId/eligibility', () =>
        apiResponse({
          student_id: 'stu1',
          target_program_id: 'p2',
          kind: 'PROMOTION',
          eligible: true,
          rules: [],
        }),
      ),
    );
    const { result } = renderHook(() => useEligibilityCheckQuery('stu1', 'PROMOTION', 'p2'), {
      wrapper: createWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.eligible).toBe(true);
  });

  it('is idle when studentId is missing', () => {
    const { result } = renderHook(() => useEligibilityCheckQuery(undefined, 'PROMOTION', 'p2'), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('is idle when targetProgramId is missing', () => {
    const { result } = renderHook(() => useEligibilityCheckQuery('stu1', 'PROMOTION', undefined), {
      wrapper: createWrapper(),
    });
    expect(result.current.fetchStatus).toBe('idle');
  });
});
