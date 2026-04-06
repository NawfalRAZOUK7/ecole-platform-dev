import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { gradebookService } from './gradebook.service';
import type { BulkGradeUpdate } from './gradebook.types';

export const gradebookQueryKeys = {
  all: ['gradebook'] as const,
  classGradebook: (classId: string) => [...gradebookQueryKeys.all, 'class', classId] as const,
  studentGrades: (studentId: string) => [...gradebookQueryKeys.all, 'student', studentId] as const,
  weightedSummary: (classId: string) =>
    [...gradebookQueryKeys.all, 'weighted-summary', classId] as const,
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
