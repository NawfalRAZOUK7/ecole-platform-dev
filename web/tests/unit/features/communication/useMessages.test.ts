import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../utils/mocks';
import { describe, it, expect } from 'vitest';
import {
  useConversations,
  useCreateConversation,
  useConversationMessages,
  useConversationReadStatus,
  useMarkConversationRead,
  useSendConversationMessage,
  useSearchMessages,
} from '@/features/communication/messages/model/useMessages';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) =>
    QueryClientProvider({ client: queryClient, children });
}

function apiListResponse<T>(data: T[]) {
  return HttpResponse.json({
    data,
    meta: {
      next_cursor: null,
      has_more: false,
      timestamp: new Date().toISOString(),
      version: 'test',
    },
  });
}

function apiResponse<T>(data: T) {
  return HttpResponse.json({
    data,
    meta: { timestamp: new Date().toISOString(), version: 'test' },
  });
}

function apiError(status = 500) {
  return HttpResponse.json(
    {
      error: { code: 'ERR', message: 'fail', category: 'system', retryable: false, timestamp: '' },
    },
    { status },
  );
}

const mockConversation = {
  id: 'conv-1',
  school_id: 'sch-1',
  type: 'direct',
  created_by: 'user-1',
  subject: 'About your child',
  participants: [
    {
      user_id: 'user-1',
      role_in_conversation: 'member',
      joined_at: '2026-01-01T00:00:00Z',
      muted: false,
    },
    {
      user_id: 'user-2',
      role_in_conversation: 'member',
      joined_at: '2026-01-01T00:00:00Z',
      muted: false,
    },
  ],
  last_message_at: '2026-09-10T09:00:00Z',
  last_message_body: 'Hello',
  unread_count: 1,
  created_at: '2026-01-01T00:00:00Z',
};

const mockMessage = {
  id: 'msg-1',
  conversation_id: 'conv-1',
  sender_id: 'user-1',
  body: 'Hello there',
  sent_at: '2026-09-10T09:00:00Z',
  edited_at: null,
  created_at: '2026-09-10T09:00:00Z',
};

const mockReadReceipt = {
  user_id: 'user-2',
  read_at: '2026-09-10T09:01:00Z',
};

describe('useConversations', () => {
  it('returns conversations on success', async () => {
    server.use(
      http.get('/api/v1/messages/conversations', () => apiListResponse([mockConversation])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useConversations(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.pages[0].data).toEqual([mockConversation]);
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/messages/conversations', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useConversations(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useCreateConversation', () => {
  it('creates a conversation', async () => {
    server.use(
      http.post('/api/v1/messages/conversations', () => apiResponse(mockConversation)),
      http.get('/api/v1/messages/conversations', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateConversation(), { wrapper });
    act(() => {
      result.current.mutate({
        type: 'direct',
        participant_ids: ['user-2'],
        initial_message: 'Hello',
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockConversation);
  });

  it('handles error', async () => {
    server.use(http.post('/api/v1/messages/conversations', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCreateConversation(), { wrapper });
    act(() =>
      result.current.mutate({ type: 'direct', participant_ids: ['user-2'], initial_message: 'Hi' }),
    );
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useConversationMessages', () => {
  it('returns messages for a conversation', async () => {
    server.use(
      http.get('/api/v1/messages/conversations/conv-1/messages', () =>
        apiListResponse([mockMessage]),
      ),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useConversationMessages('conv-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockMessage]);
  });

  it('does not fetch when conversationId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useConversationMessages(null), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('handles error', async () => {
    server.use(http.get('/api/v1/messages/conversations/conv-1/messages', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useConversationMessages('conv-1'), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useConversationReadStatus', () => {
  it('returns read status for a conversation', async () => {
    server.use(
      http.get('/api/v1/messages/conversations/conv-1/read-status', () =>
        apiListResponse([mockReadReceipt]),
      ),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useConversationReadStatus('conv-1'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockReadReceipt]);
  });

  it('does not fetch when conversationId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useConversationReadStatus(null), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});

describe('useMarkConversationRead', () => {
  it('marks conversation as read', async () => {
    server.use(
      http.post('/api/v1/messages/conversations/conv-1/read', () => apiResponse(null)),
      http.get('/api/v1/messages/conversations', () => apiListResponse([])),
      http.get('/api/v1/messages/conversations/conv-1/read-status', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useMarkConversationRead(), { wrapper });
    act(() => result.current.mutate({ conversationId: 'conv-1', messageId: 'msg-1' }));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBe('conv-1');
  });
});

describe('useSendConversationMessage', () => {
  it('sends a message', async () => {
    server.use(
      http.post('/api/v1/messages/conversations/conv-1/messages', () => apiResponse(mockMessage)),
      http.get('/api/v1/messages/conversations/conv-1/messages', () => apiListResponse([])),
      http.get('/api/v1/messages/conversations', () => apiListResponse([])),
      http.get('/api/v1/messages/conversations/conv-1/read-status', () => apiListResponse([])),
    );
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSendConversationMessage('conv-1'), { wrapper });
    act(() => result.current.mutate('Hello there'));
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockMessage);
  });

  it('handles error', async () => {
    server.use(http.post('/api/v1/messages/conversations/conv-1/messages', () => apiError()));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSendConversationMessage('conv-1'), { wrapper });
    act(() => result.current.mutate('Hello'));
    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useSearchMessages', () => {
  it('returns search results when query is long enough', async () => {
    server.use(http.get('/api/v1/messages/search', () => apiListResponse([mockMessage])));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSearchMessages('hello'), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([mockMessage]);
  });

  it('does not fetch when query is too short', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSearchMessages('a'), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('does not fetch for empty query', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSearchMessages(''), { wrapper });
    expect(result.current.fetchStatus).toBe('idle');
  });
});
