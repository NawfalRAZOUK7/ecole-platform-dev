/**
 * Chat page — conversation thread with message bubbles, read receipts, real-time via WebSocket.
 *
 * Reference: Phase 12A — Messaging UI
 * Calls GET/POST /messages/conversations/{id}/messages,
 *        POST /messages/conversations/{id}/read,
 *        GET /messages/conversations/{id}/read-status.
 * WebSocket: listens for message_created events for real-time updates.
 */

import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { wsClient, type WsEvent } from '@/services/ws/WebSocketClient';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate } from '@/shared/i18n';
import {
  useConversationMessages,
  useConversationReadStatus,
  useMarkConversationRead,
  useSendConversationMessage,
} from './useMessages';
import type { Message, ReadReceipt } from './messages.service';

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [newMessage, setNewMessage] = useState('');
  const messagesQuery = useConversationMessages(conversationId);
  const readStatusQuery = useConversationReadStatus(conversationId);
  const markReadMutation = useMarkConversationRead();
  const sendMessageMutation = useSendConversationMessage(conversationId);
  const rawMessages = messagesQuery.data ?? [];
  const messages: Message[] = useMemo(() => [...rawMessages].reverse(), [rawMessages]);
  const readReceipts = useMemo(() => {
    const map = new Map<string, ReadReceipt[]>();
    (readStatusQuery.data ?? []).forEach((receipt) => {
      const existing = map.get(receipt.user_id) || [];
      existing.push(receipt);
      map.set(receipt.user_id, existing);
    });
    return map;
  }, [readStatusQuery.data]);
  const dismissibleError = useDismissibleError(
    toBannerError(messagesQuery.error ?? sendMessageMutation.error ?? markReadMutation.error, t('app.error'))
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    const latestMessage = rawMessages[0];
    if (!conversationId || !latestMessage || latestMessage.sender_id === user?.id) {
      return;
    }
    void markReadMutation.mutateAsync({
      conversationId,
      messageId: latestMessage.id,
    }).catch(() => null);
  }, [conversationId, markReadMutation, rawMessages, user?.id]);

  useEffect(() => {
    const unsubscribe = wsClient.subscribe((event: WsEvent) => {
      if (
        event.event === 'notification_created' &&
        event.data.event_type === 'message_created' &&
        event.data.conversation_id === conversationId
      ) {
        void Promise.all([messagesQuery.refetch(), readStatusQuery.refetch()]);
      }
    });
    return unsubscribe;
  }, [conversationId, messagesQuery, readStatusQuery]);

  async function handleSend() {
    if (!newMessage.trim()) {
      return;
    }
    await sendMessageMutation.mutateAsync(newMessage.trim());
    setNewMessage('');
    await Promise.all([messagesQuery.refetch(), readStatusQuery.refetch()]);
  }

  function handleKeyDown(event: React.KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
    }
  }

  function isRead(): boolean {
    for (const [userId, receipts] of readReceipts.entries()) {
      if (userId !== user?.id && receipts.length > 0) {
        return true;
      }
    }
    return false;
  }

  if (messagesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/messages')}>
          ← {t('app.back')}
        </button>
        <h1 className="page-title" style={{ marginBottom: 0, fontSize: 20 }}>{t('messages.chat')}</h1>
      </div>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void Promise.all([messagesQuery.refetch(), readStatusQuery.refetch()])}
      />

      <div
        className="chat-messages"
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          padding: '12px 0',
        }}
      >
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--color-text-secondary)', padding: 40 }}>
            {t('messages.noMessages')}
          </div>
        ) : (
          messages.map((message) => {
            const isOwn = message.sender_id === user?.id;
            return (
              <div key={message.id} className={`chat-bubble ${isOwn ? 'chat-bubble--own' : 'chat-bubble--other'}`}>
                <div className="chat-bubble-body">{message.body}</div>
                <div className="chat-bubble-meta">
                  <span>{formatDate(message.sent_at, i18n.language, { hour: '2-digit', minute: '2-digit' })}</span>
                  {isOwn && (
                    <span className={`chat-read-indicator ${isRead() ? 'chat-read--read' : ''}`}>
                      ✓✓
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-bar">
        <textarea
          className="chat-input"
          rows={1}
          value={newMessage}
          onChange={(event) => setNewMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('messages.typePlaceholder')}
        />
        <button className="btn btn-primary" onClick={() => void handleSend()} disabled={sendMessageMutation.isPending || !newMessage.trim()}>
          {sendMessageMutation.isPending ? '...' : t('messages.send')}
        </button>
      </div>
    </div>
  );
}
