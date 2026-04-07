import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { rubricsService } from './rubrics.service';
import type { CreateRubricPayload, RubricGradePayload, UpdateRubricPayload } from './rubrics.types';

export const rubricsQueryKeys = {
  all: ['rubrics'] as const,
  list: () => [...rubricsQueryKeys.all, 'list'] as const,
  detail: (id: string) => [...rubricsQueryKeys.all, 'detail', id] as const,
  results: (id: string) => [...rubricsQueryKeys.all, 'results', id] as const,
};

export function useRubrics() {
  return useQuery({
    queryKey: rubricsQueryKeys.list(),
    queryFn: async () => (await rubricsService.listRubrics()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useRubric(id: string) {
  return useQuery({
    queryKey: rubricsQueryKeys.detail(id),
    queryFn: async () => (await rubricsService.getRubric(id)).data,
    enabled: Boolean(id),
    staleTime: STALE_DEFAULT,
  });
}

export function useRubricResults(rubricId: string) {
  return useQuery({
    queryKey: rubricsQueryKeys.results(rubricId),
    queryFn: async () => (await rubricsService.getRubricResults(rubricId)).data,
    enabled: Boolean(rubricId),
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateRubric() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateRubricPayload) =>
      (await rubricsService.createRubric(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: rubricsQueryKeys.list() });
    },
  });
}

export function useUpdateRubric() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, ...payload }: UpdateRubricPayload) =>
      (await rubricsService.updateRubric(id, { id, ...payload })).data,
    onSuccess: async (updated) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: rubricsQueryKeys.list() }),
        queryClient.invalidateQueries({ queryKey: rubricsQueryKeys.detail(updated.id) }),
      ]);
    },
  });
}

export function useDuplicateRubric() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => (await rubricsService.duplicateRubric(id)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: rubricsQueryKeys.list() });
    },
  });
}

export function useGradeRubric() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: RubricGradePayload) =>
      (await rubricsService.gradeRubric(payload)).data,
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: rubricsQueryKeys.results(result.rubric_id) });
    },
  });
}
