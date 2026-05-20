/**
 * React Query hooks for Academic Program Management (G49 Phase 2).
 *
 * Key invalidation contract:
 *   - Any program write (create/update) invalidates ['programs'].
 *   - assignProgram invalidates ['programs'] (no school-wide changes), the
 *     specific student's history/timeline/current keys, AND ['enrollments']
 *     because soft-replace creates a new enrollment row.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import {
  programsService,
  type ProgramAssignPayload,
  type ProgramCreatePayload,
  type ProgramUpdatePayload,
} from '../api/programs.api';

export const programQueryKeys = {
  all: ['programs'] as const,
  list: (activeOnly: boolean) => [...programQueryKeys.all, 'list', activeOnly] as const,
  byId: (programId: string) => [...programQueryKeys.all, 'detail', programId] as const,
  studentHistory: (studentId: string) =>
    [...programQueryKeys.all, 'student-history', studentId] as const,
  studentTimeline: (studentId: string) =>
    [...programQueryKeys.all, 'student-timeline', studentId] as const,
  studentCurrent: (studentId: string) =>
    [...programQueryKeys.all, 'student-current', studentId] as const,
  snapshotTranscript: (snapshotId: string) =>
    [...programQueryKeys.all, 'snapshot-transcript', snapshotId] as const,
};

// ---------------------------------------------------------------------------
// Catalog reads
// ---------------------------------------------------------------------------
export function useProgramsQuery(activeOnly = true, enabled = true) {
  return useQuery({
    queryKey: programQueryKeys.list(activeOnly),
    queryFn: async () => (await programsService.listPrograms(activeOnly)).data,
    enabled,
    staleTime: STALE_DEFAULT,
  });
}

export function useProgramQuery(programId: string | undefined) {
  return useQuery({
    queryKey: programId ? programQueryKeys.byId(programId) : ['programs', 'detail', 'none'],
    queryFn: async () => (await programsService.getProgram(programId!)).data,
    enabled: Boolean(programId),
    staleTime: STALE_DEFAULT,
  });
}

// ---------------------------------------------------------------------------
// Catalog writes
// ---------------------------------------------------------------------------
export function useCreateProgramMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: ProgramCreatePayload) =>
      (await programsService.createProgram(body)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: programQueryKeys.all });
    },
  });
}

export function useUpdateProgramMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { programId: string; body: ProgramUpdatePayload }) =>
      (await programsService.updateProgram(vars.programId, vars.body)).data,
    onSuccess: async (program) => {
      await queryClient.invalidateQueries({ queryKey: programQueryKeys.all });
      await queryClient.invalidateQueries({
        queryKey: programQueryKeys.byId(program.id),
      });
    },
  });
}

// ---------------------------------------------------------------------------
// Assignment
// ---------------------------------------------------------------------------
export function useAssignProgramMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (vars: {
      enrollmentId: string;
      body: ProgramAssignPayload;
      // Optional: passed by callers so we can invalidate the right student's
      // history/timeline/current views without a refetch heuristic.
      studentId?: string;
    }) => (await programsService.assignProgram(vars.enrollmentId, vars.body)).data,
    onSuccess: async (_event, vars) => {
      // Soft-replace creates a new enrollment row, so any list of enrollments
      // is potentially stale.
      await queryClient.invalidateQueries({ queryKey: ['enrollments'] });
      if (vars.studentId) {
        await queryClient.invalidateQueries({
          queryKey: programQueryKeys.studentHistory(vars.studentId),
        });
        await queryClient.invalidateQueries({
          queryKey: programQueryKeys.studentTimeline(vars.studentId),
        });
        await queryClient.invalidateQueries({
          queryKey: programQueryKeys.studentCurrent(vars.studentId),
        });
      }
    },
  });
}

// ---------------------------------------------------------------------------
// Student academic history reads
// ---------------------------------------------------------------------------
export function useStudentProgramHistoryQuery(studentId: string | undefined) {
  return useQuery({
    queryKey: studentId
      ? programQueryKeys.studentHistory(studentId)
      : ['programs', 'student-history', 'none'],
    queryFn: async () => (await programsService.getProgramHistory(studentId!)).data,
    enabled: Boolean(studentId),
    staleTime: STALE_DEFAULT,
  });
}

export function useStudentAcademicTimelineQuery(studentId: string | undefined) {
  return useQuery({
    queryKey: studentId
      ? programQueryKeys.studentTimeline(studentId)
      : ['programs', 'student-timeline', 'none'],
    queryFn: async () => (await programsService.getAcademicTimeline(studentId!)).data,
    enabled: Boolean(studentId),
    staleTime: STALE_DEFAULT,
  });
}

export function useStudentCurrentProgramQuery(studentId: string | undefined) {
  return useQuery({
    queryKey: studentId
      ? programQueryKeys.studentCurrent(studentId)
      : ['programs', 'student-current', 'none'],
    queryFn: async () => (await programsService.getCurrentProgram(studentId!)).data,
    enabled: Boolean(studentId),
    staleTime: STALE_DEFAULT,
  });
}

// ---------------------------------------------------------------------------
// Phase 3.1 — Program versions
// ---------------------------------------------------------------------------
export function useProgramVersionsQuery(programId: string | undefined) {
  return useQuery({
    queryKey: programId
      ? [...programQueryKeys.all, 'versions', programId]
      : ['programs', 'versions', 'none'],
    queryFn: async () => (await programsService.listProgramVersions(programId!)).data,
    enabled: Boolean(programId),
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateProgramVersionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (vars: {
      programId: string;
      body: {
        version_label: string;
        description?: string | null;
        effective_from?: string | null;
        is_active?: boolean;
      };
    }) => (await programsService.createProgramVersion(vars.programId, vars.body)).data,
    onSuccess: async (_v, vars) => {
      await queryClient.invalidateQueries({
        queryKey: [...programQueryKeys.all, 'versions', vars.programId],
      });
    },
  });
}

export function useUpdateProgramVersionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (vars: {
      programId: string;
      versionId: string;
      body: {
        description?: string | null;
        effective_from?: string | null;
        retired_at?: string | null;
        is_active?: boolean;
      };
    }) =>
      (await programsService.updateProgramVersion(vars.programId, vars.versionId, vars.body)).data,
    onSuccess: async (_v, vars) => {
      await queryClient.invalidateQueries({
        queryKey: [...programQueryKeys.all, 'versions', vars.programId],
      });
    },
  });
}

// ---------------------------------------------------------------------------
// Phase 3.2 — Equivalences
// ---------------------------------------------------------------------------
export function useProgramEquivalencesQuery(programId?: string) {
  return useQuery({
    queryKey: [...programQueryKeys.all, 'equivalences', programId ?? 'all'],
    queryFn: async () => (await programsService.listProgramEquivalences(programId)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateEquivalenceMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      from_program_id: string;
      to_program_id: string;
      kind: 'EQUIVALENT' | 'SUPERSEDES' | 'PARTIAL';
      note?: string | null;
      ratified_at?: string | null;
    }) => (await programsService.createProgramEquivalence(body)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: [...programQueryKeys.all, 'equivalences'],
      });
    },
  });
}

export function useDeleteEquivalenceMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => (await programsService.deleteProgramEquivalence(id)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: [...programQueryKeys.all, 'equivalences'],
      });
    },
  });
}

// ---------------------------------------------------------------------------
// Phase 3.3 — Academic snapshots
// ---------------------------------------------------------------------------
export function useStudentSnapshotsQuery(studentId: string | undefined) {
  return useQuery({
    queryKey: studentId
      ? [...programQueryKeys.all, 'snapshots', studentId]
      : ['programs', 'snapshots', 'none'],
    queryFn: async () => (await programsService.listStudentSnapshots(studentId!)).data,
    enabled: Boolean(studentId),
    staleTime: STALE_DEFAULT,
  });
}

export function useTakeSnapshotMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      student_id: string;
      academic_year_id: string;
      snapshot_kind?: 'YEAR_END' | 'MID_YEAR' | 'MANUAL';
    }) => (await programsService.takeSnapshot(body)).data,
    onSuccess: async (_data, vars) => {
      await queryClient.invalidateQueries({
        queryKey: [...programQueryKeys.all, 'snapshots', vars.student_id],
      });
    },
  });
}

export function useSnapshotTranscriptMutation() {
  return useMutation({
    mutationFn: async (snapshotId: string) =>
      (await programsService.getSnapshotTranscript(snapshotId)).data,
  });
}

export function useSnapshotTranscriptHtmlMutation() {
  return useMutation({
    mutationFn: async (snapshotId: string) => programsService.getSnapshotTranscriptHtml(snapshotId),
  });
}

export function useStudentTranscriptHtmlMutation() {
  return useMutation({
    mutationFn: async (vars: {
      studentId: string;
      academicYearId: string;
      mode?: 'preview' | 'snapshot';
    }) =>
      programsService.getStudentTranscriptHtml(
        vars.studentId,
        vars.academicYearId,
        vars.mode ?? 'preview',
      ),
  });
}

export function useSnapshotTranscriptPdfMutation() {
  return useMutation({
    mutationFn: async (snapshotId: string) =>
      programsService.downloadSnapshotTranscriptPdf(snapshotId),
  });
}

export function useStudentTranscriptPdfMutation() {
  return useMutation({
    mutationFn: async (vars: {
      studentId: string;
      academicYearId: string;
      mode?: 'preview' | 'snapshot';
    }) =>
      programsService.downloadStudentTranscriptPdf(
        vars.studentId,
        vars.academicYearId,
        vars.mode ?? 'preview',
      ),
  });
}

// ---------------------------------------------------------------------------
// Phase 3.4 — Eligibility
// ---------------------------------------------------------------------------
export function useEligibilityRulesQuery(
  filters: {
    kind?: 'PROMOTION' | 'ADMISSION' | 'TRANSFER';
    target_program_id?: string;
    active_only?: boolean;
  } = {},
) {
  return useQuery({
    queryKey: [
      ...programQueryKeys.all,
      'eligibility-rules',
      filters.kind ?? 'all',
      filters.target_program_id ?? 'all',
      filters.active_only === false ? 'all' : 'active',
    ],
    queryFn: async () => (await programsService.listEligibilityRules(filters)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateEligibilityRuleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      kind: 'PROMOTION' | 'ADMISSION' | 'TRANSFER';
      target_program_id: string;
      condition_type: string;
      condition_params?: Record<string, unknown>;
      message_key: string;
      is_active?: boolean;
    }) => (await programsService.createEligibilityRule(body)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: [...programQueryKeys.all, 'eligibility-rules'],
      });
    },
  });
}

export function useDeleteEligibilityRuleMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (ruleId: string) =>
      (await programsService.deleteEligibilityRule(ruleId)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: [...programQueryKeys.all, 'eligibility-rules'],
      });
    },
  });
}

export function useEligibilityCheckQuery(
  studentId: string | undefined,
  kind: 'PROMOTION' | 'ADMISSION' | 'TRANSFER',
  targetProgramId: string | undefined,
) {
  return useQuery({
    queryKey: [
      ...programQueryKeys.all,
      'eligibility',
      studentId ?? 'none',
      kind,
      targetProgramId ?? 'none',
    ],
    queryFn: async () =>
      (await programsService.checkEligibility(studentId!, kind, targetProgramId!)).data,
    enabled: Boolean(studentId && targetProgramId),
    staleTime: STALE_DEFAULT,
  });
}
