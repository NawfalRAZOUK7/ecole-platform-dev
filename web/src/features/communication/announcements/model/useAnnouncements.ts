import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import {
  announcementsService,
  type AnnouncementFilters,
  type AnnouncementInput,
} from '../api/announcements.api';

export const announcementsQueryKeys = {
  all: ['announcements'] as const,
  list: (filters: Omit<AnnouncementFilters, 'cursor'>) =>
    [...announcementsQueryKeys.all, 'list', filters] as const,
};

export function useAnnouncements(filters: Omit<AnnouncementFilters, 'cursor'>) {
  return useInfiniteQuery({
    queryKey: announcementsQueryKeys.list(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      announcementsService.list({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateAnnouncement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: AnnouncementInput) => {
      await announcementsService.create(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: announcementsQueryKeys.all });
    },
  });
}

export function useUpdateAnnouncement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      announcementId,
      payload,
    }: {
      announcementId: string;
      payload: AnnouncementInput;
    }) => {
      await announcementsService.update(announcementId, payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: announcementsQueryKeys.all });
    },
  });
}

export function usePublishAnnouncement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (announcementId: string) => {
      await announcementsService.publish(announcementId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: announcementsQueryKeys.all });
    },
  });
}
