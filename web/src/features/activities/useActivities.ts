import { useInfiniteQuery } from '@tanstack/react-query';
import { STALE_CONTENT } from '@/shared/hooks/useQueryDefaults';
import { activitiesService, type ActivityFilters } from './activities.service';

export const activitiesQueryKeys = {
  all: ['activities'] as const,
  list: (filters: Omit<ActivityFilters, 'cursor'>) => [...activitiesQueryKeys.all, 'list', filters] as const,
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
