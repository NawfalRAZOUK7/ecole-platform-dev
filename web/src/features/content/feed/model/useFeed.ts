import { useEffect, useMemo, useState } from 'react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { STALE_FEED } from '@/shared/hooks/useQueryDefaults';
import { feedService, type FeedListParams } from '../api/feed.api';

export const feedQueryKeys = {
  all: ['feed'] as const,
  list: (filters: Omit<FeedListParams, 'cursor'>) =>
    [...feedQueryKeys.all, 'list', filters] as const,
  unreadSummary: () => [...feedQueryKeys.all, 'unread-summary'] as const,
};

export function useFeed(filters: Omit<FeedListParams, 'cursor'> = {}) {
  return useInfiniteQuery({
    queryKey: feedQueryKeys.list(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) => feedService.list({ ...filters, cursor: pageParam }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_FEED,
  });
}

export function useFeedUnreadSummary(enabled: boolean) {
  const [version, setVersion] = useState(0);
  const summaryQuery = useQuery({
    queryKey: feedQueryKeys.unreadSummary(),
    queryFn: async () => (await feedService.list({ limit: 50 })).data,
    enabled,
    staleTime: STALE_FEED,
  });

  useEffect(() => {
    return feedService.subscribeToReadChanges(() => {
      setVersion((current) => current + 1);
    });
  }, []);

  const unreadCount = useMemo(
    () => feedService.countUnread(summaryQuery.data ?? []),
    [summaryQuery.data, version],
  );

  return {
    ...summaryQuery,
    unreadCount,
  };
}
