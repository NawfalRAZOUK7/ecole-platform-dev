import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT, STALE_NOTIFICATIONS } from '@/shared/hooks/useQueryDefaults';
import { messagesService } from '../api/messages.api';

export const messagesQueryKeys = {
  all: ['messages'] as const,
  conversations: () => [...messagesQueryKeys.all, 'conversations'] as const,
  conversationMessages: (conversationId: string | null | undefined) =>
    [...messagesQueryKeys.all, 'conversation', conversationId, 'messages'] as const,
  readStatus: (conversationId: string | null | undefined) =>
    [...messagesQueryKeys.all, 'conversation', conversationId, 'read-status'] as const,
  search: (query: string) => [...messagesQueryKeys.all, 'search', query] as const,
};

export function useConversations() {
  return useInfiniteQuery({
    queryKey: messagesQueryKeys.conversations(),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      messagesService.listConversations({
        limit: 20,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_NOTIFICATIONS,
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      type: string;
      participant_ids: string[];
      subject?: string;
      initial_message: string;
    }) => (await messagesService.createConversation(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: messagesQueryKeys.conversations() });
    },
  });
}

export function useConversationMessages(conversationId: string | null | undefined) {
  return useQuery({
    queryKey: messagesQueryKeys.conversationMessages(conversationId),
    queryFn: async () =>
      (await messagesService.listConversationMessages(conversationId!, { limit: 50 })).data,
    enabled: Boolean(conversationId),
    staleTime: STALE_DEFAULT,
  });
}

export function useConversationReadStatus(conversationId: string | null | undefined) {
  return useQuery({
    queryKey: messagesQueryKeys.readStatus(conversationId),
    queryFn: async () => (await messagesService.listConversationReadStatus(conversationId!)).data,
    enabled: Boolean(conversationId),
    staleTime: STALE_NOTIFICATIONS,
  });
}

export function useMarkConversationRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      conversationId,
      messageId,
    }: {
      conversationId: string;
      messageId: string;
    }) => {
      await messagesService.markConversationRead(conversationId, messageId);
      return conversationId;
    },
    onSuccess: async (conversationId) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: messagesQueryKeys.conversations() }),
        queryClient.invalidateQueries({ queryKey: messagesQueryKeys.readStatus(conversationId) }),
      ]);
    },
  });
}

export function useSendConversationMessage(conversationId: string | null | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (body: string) =>
      (await messagesService.sendConversationMessage(conversationId!, body)).data,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: messagesQueryKeys.conversationMessages(conversationId),
        }),
        queryClient.invalidateQueries({ queryKey: messagesQueryKeys.conversations() }),
        queryClient.invalidateQueries({ queryKey: messagesQueryKeys.readStatus(conversationId) }),
      ]);
    },
  });
}

export function useSearchMessages(query: string) {
  return useQuery({
    queryKey: messagesQueryKeys.search(query),
    queryFn: async () => (await messagesService.searchMessages(query)).data,
    enabled: query.trim().length >= 2,
    staleTime: STALE_DEFAULT,
  });
}
