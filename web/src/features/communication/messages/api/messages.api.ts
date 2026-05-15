import { api } from '@/core/api/client';

export interface Participant {
  user_id: string;
  role_in_conversation: string;
  joined_at: string;
  muted: boolean;
}

export interface Conversation {
  id: string;
  school_id: string;
  type: string;
  created_by: string;
  subject: string | null;
  participants: Participant[];
  last_message_at: string | null;
  last_message_body: string | null;
  unread_count: number;
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  body: string;
  sent_at: string;
  edited_at: string | null;
  created_at: string;
}

export interface ReadReceipt {
  user_id: string;
  read_at: string;
}

export const messagesService = {
  listConversations(params: Record<string, string | number | undefined>) {
    return api.list<Conversation>('/messages/conversations', params);
  },

  createConversation(payload: {
    type: string;
    participant_ids: string[];
    subject?: string;
    initial_message: string;
  }) {
    return api.post<Conversation>('/messages/conversations', payload);
  },

  listConversationMessages(
    conversationId: string,
    params: Record<string, string | number | undefined>,
  ) {
    return api.list<Message>(`/messages/conversations/${conversationId}/messages`, params);
  },

  markConversationRead(conversationId: string, messageId: string) {
    return api.post<void>(`/messages/conversations/${conversationId}/read`, {
      message_id: messageId,
    });
  },

  listConversationReadStatus(conversationId: string) {
    return api.list<ReadReceipt>(`/messages/conversations/${conversationId}/read-status`);
  },

  sendConversationMessage(conversationId: string, body: string) {
    return api.post<Message>(`/messages/conversations/${conversationId}/messages`, { body });
  },

  searchMessages(query: string) {
    return api.list<Message>('/messages/search', { q: query });
  },
};
