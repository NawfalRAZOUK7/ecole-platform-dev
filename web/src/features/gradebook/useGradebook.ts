import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { gradebookService } from './gradebook.service';
import type { BulkGradeUpdate, CreateCategoryPayload } from './gradebook.types';

export const gradebookQueryKeys = {
  all: ['gradebook'] as const,
  classGradebook: (classId: string, periodId: string) =>
    [...gradebookQueryKeys.all, 'class', classId, periodId] as const,
  periodGradebook: (classId: string, period: string) =>
    [...gradebookQueryKeys.all, 'class', classId, 'period', period] as const,
  studentGrades: (studentId: string) => [...gradebookQueryKeys.all, 'student', studentId] as const,
  transcript: (studentId: string, academicYear?: string) =>
    [...gradebookQueryKeys.all, 'transcript', studentId, academicYear ?? 'current'] as const,
  weightedSummary: (classId: string, periodId: string) =>
    [...gradebookQueryKeys.all, 'weighted-summary', classId, periodId] as const,
  categories: (classId: string, periodId: string) =>
    [...gradebookQueryKeys.all, 'categories', classId, periodId] as const,
};

export function useClassGradebook(classId: string, periodId: string) {
  return useQuery({
    queryKey: gradebookQueryKeys.classGradebook(classId, periodId),
    queryFn: async () => (await gradebookService.getClassGradebook(classId, periodId)).data,
    enabled: Boolean(classId && periodId),
    staleTime: STALE_DEFAULT,
  });
}

export function useStudentGrades(studentId: string, academicYearId?: string) {
  return useQuery({
    queryKey: gradebookQueryKeys.studentGrades(studentId),
    queryFn: async () => (await gradebookService.getStudentGrades(studentId, academicYearId)).data,
    enabled: Boolean(studentId),
    staleTime: STALE_DEFAULT,
  });
}

export function useUpdateGrades() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: BulkGradeUpdate) => {
      await gradebookService.updateGrades(payload);
      return payload.class_id;
    },
    onSuccess: async (classId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: [...gradebookQueryKeys.all, 'class', classId] }),
        queryClient.invalidateQueries({
          queryKey: [...gradebookQueryKeys.all, 'weighted-summary', classId],
        }),
      ]);
    },
  });
}

export function useWeightedSummary(classId: string, periodId: string) {
  return useQuery({
    queryKey: gradebookQueryKeys.weightedSummary(classId, periodId),
    queryFn: async () => (await gradebookService.getWeightedSummary(classId, periodId)).data,
    enabled: Boolean(classId && periodId),
    staleTime: STALE_DEFAULT,
  });
}

export function useGradebookCategories(classId: string, periodId: string) {
  return useQuery({
    queryKey: gradebookQueryKeys.categories(classId, periodId),
    queryFn: async () => (await gradebookService.getCategories(classId, periodId)).data,
    enabled: Boolean(classId && periodId),
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateGradebookCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateCategoryPayload) => gradebookService.createCategory(payload),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: [...gradebookQueryKeys.all, 'categories', variables.class_id],
      });
    },
  });
}

export function useComputeGrades() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ classId, periodId }: { classId: string; periodId: string }) =>
      gradebookService.computeGrades(classId, periodId),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: gradebookQueryKeys.classGradebook(variables.classId, variables.periodId),
        }),
        queryClient.invalidateQueries({
          queryKey: gradebookQueryKeys.weightedSummary(variables.classId, variables.periodId),
        }),
      ]);
    },
  });
}

export function useGradebookTranscript(studentId: string, academicYear?: string) {
  return useQuery({
    queryKey: gradebookQueryKeys.transcript(studentId, academicYear),
    queryFn: async () => (await gradebookService.getTranscript(studentId, academicYear)).data,
    enabled: Boolean(studentId),
    staleTime: STALE_DEFAULT,
  });
}

export function usePeriodGradebook(classId: string, period: string) {
  return useQuery({
    queryKey: gradebookQueryKeys.periodGradebook(classId, period),
    queryFn: async () => (await gradebookService.getPeriodGradebook(classId, period)).data,
    enabled: Boolean(classId && period),
    staleTime: STALE_DEFAULT,
  });
}
