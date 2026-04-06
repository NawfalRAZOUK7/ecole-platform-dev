import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { STALE_CONTENT } from '@/shared/hooks/useQueryDefaults';
import { activitiesService, type ActivityFilters } from './activities.service';

export const activitiesQueryKeys = {
  all: ['activities'] as const,
  list: (filters: Omit<ActivityFilters, 'cursor'>) =>
    [...activitiesQueryKeys.all, 'list', filters] as const,
  detail: (activityId: string) => [...activitiesQueryKeys.all, 'detail', activityId] as const,
};

export function useActivities(filters: Omit<ActivityFilters, 'cursor'> = {}) {
  return useInfiniteQuery({
    queryKey: activitiesQueryKeys.list(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      activitiesService.list({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_CONTENT,
  });
}

export function useActivityDetail(activityId: string) {
  return useQuery({
    queryKey: activitiesQueryKeys.detail(activityId),
    queryFn: async () => (await activitiesService.getDetail(activityId)).data,
    enabled: Boolean(activityId),
    staleTime: STALE_CONTENT,
  });
}

export function useCreateActivitySession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ activityId }: { activityId: string }) =>
      activitiesService.createSession(activityId),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: activitiesQueryKeys.detail(variables.activityId) }),
        queryClient.invalidateQueries({ queryKey: activitiesQueryKeys.all }),
      ]);
    },
  });
}

export function useCompleteActivitySession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (variables: {
      activityId: string;
      sessionId: string;
      score?: number;
    }) => activitiesService.completeSession(variables.sessionId, variables.score),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: activitiesQueryKeys.detail(variables.activityId) }),
        queryClient.invalidateQueries({ queryKey: activitiesQueryKeys.all }),
      ]);
    },
  });
}
