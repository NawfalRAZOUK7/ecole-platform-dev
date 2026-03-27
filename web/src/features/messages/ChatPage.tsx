/**
 * Chat page — conversation thread with message bubbles, read receipts, real-time via WebSocket.
 *
 * Reference: Phase 12A — Messaging UI
 * Calls GET/POST /messages/conversations/{id}/messages,
 *        POST /messages/conversations/{id}/read,
 *        GET /messages/conversations/{id}/read-status.
 * WebSocket: listens for message_created events for real-time updates.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/services/auth/AuthContext';
import { api, ApiClientError } from '@/services/api/client';
import { wsClient, type WsEvent } from '@/services/ws/WebSocketClient';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { formatDate } from '@/shared/i18n';

interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  body: string;
  sent_at: string;
  edited_at: string | null;
  created_at: string;
}

interface ReadReceipt {
  user_id: string;
  read_at: string;
}

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [readReceipts, setReadReceipts] = useState<Map<string, ReadReceipt[]>>(new Map());

  const fetchMessages = useCallback(async () => {
    if (!conversationId) return;
    try {
      const resp = await api.list<Message>(`/messages/conversations/${conversationId}/messages`, { limit: 50 });
      // API returns newest first; reverse for display
      setMessages(resp.data.reverse());
      setError(null);

      // Mark latest message as read
      if (resp.data.length > 0) {
        const latestId = resp.data[0].id; // newest message (pre-reverse)
        await api.post(`/messages/conversations/${conversationId}/read`, { message_id: latestId }).catch(() => {});
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [conversationId, t]);

  const fetchReadStatus = useCallback(async () => {
    if (!conversationId) return;
    try {
      const resp = await api.list<ReadReceipt>(`/messages/conversations/${conversationId}/read-status`);
      // Group by user for display
      const map = new Map<string, ReadReceipt[]>();
      resp.data.forEach((r) => {
        const existing = map.get(r.user_id) || [];
        existing.push(r);
        map.set(r.user_id, existing);
      });
      setReadReceipts(map);
    } catch {
      // Non-critical
    }
  }, [conversationId]);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchMessages(), fetchReadStatus()]).finally(() => setLoading(false));
  }, [fetchMessages, fetchReadStatus]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // WebSocket: listen for new messages in this conversation
  useEffect(() => {
    const unsub = wsClient.subscribe((event: WsEvent) => {
      if (
        event.event === 'notification_created' &&
        event.data.event_type === 'message_created' &&
        event.data.conversation_id === conversationId
      ) {
        // Refetch messages
        fetchMessages();
      }
    });
    return unsub;
  }, [conversationId, fetchMessages]);

  async function handleSend() {
    if (!newMessage.trim() || !conversationId) return;
    const text = newMessage.trim();
    // Optimistic append
    const tempId = `temp-${Date.now()}`;
    const optimistic: Message = {
      id: tempId,
      conversation_id: conversationId,
      sender_id: user?.id || '',
      body: text,
      sent_at: new Date().toISOString(),
      edited_at: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);
    setNewMessage('');
    setSending(true);
    try {
      const resp = await api.post<Message>(`/messages/conversations/${conversationId}/messages`, {
        body: text,
      });
      // Replace optimistic with server version
      setMessages((prev) => prev.map((m) => m.id === tempId ? resp.data : m));
    } catch (err) {
      // Remove optimistic on failure
      setMessages((prev) => prev.filter((m) => m.id !== tempId));
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // Check if a message has been read by at least one other participant
  function isRead(): boolean {
    for (const [userId, receipts] of readReceipts.entries()) {
      if (userId !== user?.id && receipts.length > 0) {
        return true;
      }
    }
    return false;
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 64px)' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/messages')}>
          ← {t('app.back')}
        </button>
        <h1 className="page-title" style={{ marginBottom: 0, fontSize: 20 }}>{t('messages.chat')}</h1>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchMessages} />

      {/* Messages */}
      <div className="chat-messages" style={{
        flex: 1,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        padding: '12px 0',
      }}>
        {messages.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--color-text-secondary)', padding: 40 }}>
            {t('messages.noMessages')}
          </div>
        ) : (
          messages.map((msg) => {
            const isOwn = msg.sender_id === user?.id;
            return (
              <div
                key={msg.id}
                className={`chat-bubble ${isOwn ? 'chat-bubble--own' : 'chat-bubble--other'}`}
              >
                <div className="chat-bubble-body">{msg.body}</div>
                <div className="chat-bubble-meta">
                  <span>{formatDate(msg.sent_at, i18n.language, { hour: '2-digit', minute: '2-digit' })}</span>
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

      {/* Input */}
      <div className="chat-input-bar">
        <textarea
          className="chat-input"
          rows={1}
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={t('messages.typePlaceholder')}
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={sending || !newMessage.trim()}
        >
          {sending ? '...' : t('messages.send')}
        </button>
      </div>
    </div>
  );
}
