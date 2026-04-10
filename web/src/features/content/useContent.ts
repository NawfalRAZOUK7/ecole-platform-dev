import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_CONTENT } from '@/shared/hooks/useQueryDefaults';
import { contentService, type ContentFilters, type ContentProgressStatus } from './content.service';

export const contentQueryKeys = {
  all: ['content'] as const,
  items: (filters: Omit<ContentFilters, 'cursor'>) =>
    [...contentQueryKeys.all, 'items', filters] as const,
  detail: (contentId: string) => [...contentQueryKeys.all, 'detail', contentId] as const,
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
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_CONTENT,
  });
}

export function useContentDetail(contentId: string) {
  return useQuery({
    queryKey: contentQueryKeys.detail(contentId),
    queryFn: async () => (await contentService.getContentItem(contentId)).data,
    enabled: Boolean(contentId),
    staleTime: STALE_CONTENT,
  });
}

export function useUpdateContentProgress() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      contentId,
      status,
    }: {
      contentId: string;
      status: ContentProgressStatus;
    }) => contentService.updateProgress(contentId, status),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: contentQueryKeys.detail(variables.contentId) }),
        queryClient.invalidateQueries({ queryKey: contentQueryKeys.all }),
      ]);
    },
  });
}

export function useToggleContentPublish() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      contentId,
      status,
    }: {
      contentId: string;
      status: 'draft' | 'published';
    }) => contentService.togglePublish(contentId, status),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: contentQueryKeys.detail(variables.contentId) }),
        queryClient.invalidateQueries({ queryKey: contentQueryKeys.all }),
      ]);
    },
  });
}

export function useUpdateContentOrdering() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ contentId, sortOrder }: { contentId: string; sortOrder: number }) =>
      contentService.updateOrdering(contentId, sortOrder),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: contentQueryKeys.detail(variables.contentId) }),
        queryClient.invalidateQueries({ queryKey: contentQueryKeys.all }),
      ]);
    },
  });
}

export function useStreamContent(contentItemId: string) {
  return useQuery({
    queryKey: [...contentQueryKeys.all, 'stream', contentItemId] as const,
    queryFn: async () => (await contentService.streamContent(contentItemId)).data,
    enabled: Boolean(contentItemId),
    staleTime: STALE_CONTENT,
  });
}

export function useContentAsset(contentItemId: string, assetId: string) {
  return useQuery({
    queryKey: [...contentQueryKeys.all, 'asset', contentItemId, assetId] as const,
    queryFn: async () => (await contentService.getAsset(contentItemId, assetId)).data,
    enabled: Boolean(contentItemId && assetId),
    staleTime: STALE_CONTENT,
  });
}

export function useDeleteContentAsset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ contentItemId, assetId }: { contentItemId: string; assetId: string }) => {
      await contentService.deleteAsset(contentItemId, assetId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: contentQueryKeys.all });
    },
  });
}
