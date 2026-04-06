import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { gradebookService } from './gradebook.service';
import type { BulkGradeUpdate, CreateCategoryPayload } from './gradebook.types';

export const gradebookQueryKeys = {
  all: ['gradebook'] as const,
  classGradebook: (classId: string) => [...gradebookQueryKeys.all, 'class', classId] as const,
  periodGradebook: (classId: string, period: string) =>
    [...gradebookQueryKeys.all, 'class', classId, 'period', period] as const,
  studentGrades: (studentId: string) => [...gradebookQueryKeys.all, 'student', studentId] as const,
  transcript: (studentId: string, academicYear?: string) =>
    [...gradebookQueryKeys.all, 'transcript', studentId, academicYear ?? 'current'] as const,
  weightedSummary: (classId: string) =>
    [...gradebookQueryKeys.all, 'weighted-summary', classId] as const,
  categories: (classId: string) => [...gradebookQueryKeys.all, 'categories', classId] as const,
};

export function useClassGradebook(classId: string) {
  return useQuery({
    queryKey: gradebookQueryKeys.classGradebook(classId),
    queryFn: async () => (await gradebookService.getClassGradebook(classId)).data,
    enabled: Boolean(classId),
    staleTime: STALE_DEFAULT,
  });
}

export function useStudentGrades(studentId: string) {
  return useQuery({
    queryKey: gradebookQueryKeys.studentGrades(studentId),
    queryFn: async () => (await gradebookService.getStudentGrades(studentId)).data,
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
        queryClient.invalidateQueries({ queryKey: gradebookQueryKeys.classGradebook(classId) }),
        queryClient.invalidateQueries({ queryKey: gradebookQueryKeys.weightedSummary(classId) }),
      ]);
    },
  });
}

export function useWeightedSummary(classId: string) {
  return useQuery({
    queryKey: gradebookQueryKeys.weightedSummary(classId),
    queryFn: async () => (await gradebookService.getWeightedSummary(classId)).data,
    enabled: Boolean(classId),
    staleTime: STALE_DEFAULT,
  });
}

export function useGradebookCategories(classId: string) {
  return useQuery({
    queryKey: gradebookQueryKeys.categories(classId),
    queryFn: async () => (await gradebookService.getCategories(classId)).data,
    enabled: Boolean(classId),
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateGradebookCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateCategoryPayload) => gradebookService.createCategory(payload),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: gradebookQueryKeys.categories(variables.class_id),
      });
    },
  });
}

export function useComputeGrades() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (classId: string) => gradebookService.computeGrades(classId),
    onSuccess: async (_data, classId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: gradebookQueryKeys.classGradebook(classId) }),
        queryClient.invalidateQueries({ queryKey: gradebookQueryKeys.weightedSummary(classId) }),
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
