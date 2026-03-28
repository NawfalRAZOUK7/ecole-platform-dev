import { useInfiniteQuery } from '@tanstack/react-query';
import { STALE_CONTENT } from '@/shared/hooks/useQueryDefaults';
import { contentService, type ContentFilters } from './content.service';

export const contentQueryKeys = {
  all: ['content'] as const,
  items: (filters: Omit<ContentFilters, 'cursor'>) => [...contentQueryKeys.all, 'items', filters] as const,
};

export function useContentItems(filters: Omit<ContentFilters, 'cursor'>) {
  return useInfiniteQuery({
    queryKey: contentQueryKeys.items(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      contentService.listContentItems({
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_CONTENT,
  });
}
