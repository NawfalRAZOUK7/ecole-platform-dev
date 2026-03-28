import { useInfiniteQuery } from '@tanstack/react-query';
import { STALE_FEED } from '@/shared/hooks/useQueryDefaults';
import { feedService } from './feed.service';

export const feedQueryKeys = {
  all: ['feed'] as const,
  list: () => [...feedQueryKeys.all, 'list'] as const,
};

export function useFeed() {
  return useInfiniteQuery({
    queryKey: feedQueryKeys.list(),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) => feedService.list({ cursor: pageParam }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_FEED,
  });
}
