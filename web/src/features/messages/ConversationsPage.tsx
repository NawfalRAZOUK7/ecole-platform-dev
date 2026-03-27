/**
 * Conversations page — inbox-style list of conversations.
 *
 * Reference: Phase 12A — Messaging UI
 * Calls GET /messages/conversations (cursor-paginated).
 * "New Message" button starts a new conversation via POST /messages/conversations.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/services/auth/AuthContext';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface Participant {
  user_id: string;
  role_in_conversation: string;
  joined_at: string;
  muted: boolean;
}

interface Conversation {
  id: string;
  school_id: string;
  type: string;
  created_by: string;
  subject: string | null;
  participants: Participant[];
  last_message_at: string | null;
  created_at: string;
}

export function ConversationsPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [items, setItems] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  // New conversation form
  const [showNew, setShowNew] = useState(false);
  const [newParticipant, setNewParticipant] = useState('');
  const [newSubject, setNewSubject] = useState('');
  const [newMessage, setNewMessage] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchConversations = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = { limit: 20 };
      if (cursor) params.cursor = cursor;
      const resp = await api.list<Conversation>('/messages/conversations', params);
      if (cursor) {
        setItems((prev) => [...prev, ...resp.data]);
      } else {
        setItems(resp.data);
      }
      setNextCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchConversations().finally(() => setLoading(false));
  }, [fetchConversations]);

  async function handleCreate() {
    setCreating(true);
    try {
      const resp = await api.post<Conversation>('/messages/conversations', {
        type: 'DIRECT',
        participant_ids: [newParticipant],
        subject: newSubject || undefined,
        initial_message: newMessage,
      });
      setShowNew(false);
      setNewParticipant('');
      setNewSubject('');
      setNewMessage('');
      // Navigate to new conversation
      navigate(`/messages/${resp.data.id}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setCreating(false);
    }
  }

  function getOtherParticipant(conv: Conversation): string {
    const other = conv.participants.find((p) => p.user_id !== user?.id);
    if (other) return other.user_id.slice(0, 8) + '...';
    return conv.subject || t('messages.conversation');
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>{t('messages.title')}</h1>
        <button className="btn btn-primary" onClick={() => setShowNew(true)}>
          + {t('messages.newConversation')}
        </button>
      </div>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchConversations()} />

      {items.length === 0 ? (
        <EmptyState message={t('messages.empty')} icon="💬" />
      ) : (
        <div className="card-list">
          {items.map((conv) => (
            <div
              key={conv.id}
              className="card conversation-card"
              onClick={() => navigate(`/messages/${conv.id}`)}
              style={{ cursor: 'pointer' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>
                    {conv.subject || getOtherParticipant(conv)}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 2 }}>
                    {conv.type === 'DIRECT' ? t('messages.direct') : t('messages.group')}
                    {' · '}
                    {conv.participants.length} {t('messages.participants')}
                  </div>
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
                  {conv.last_message_at ? formatDate(conv.last_message_at, i18n.language) : formatDate(conv.created_at, i18n.language)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button className="btn btn-secondary" onClick={() => fetchConversations(nextCursor || undefined)}>
            {t('feed.loadMore')}
          </button>
        </div>
      )}

      {/* New Conversation Modal */}
      {showNew && (
        <div className="modal-overlay" onClick={() => setShowNew(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>{t('messages.newConversation')}</h2>
            <div className="form-field">
              <label>{t('messages.recipient')}</label>
              <input
                type="text"
                value={newParticipant}
                onChange={(e) => setNewParticipant(e.target.value)}
                placeholder={t('messages.recipientPlaceholder')}
              />
            </div>
            <div className="form-field">
              <label>{t('messages.subject')}</label>
              <input
                type="text"
                value={newSubject}
                onChange={(e) => setNewSubject(e.target.value)}
                placeholder={t('messages.subjectPlaceholder')}
              />
            </div>
            <div className="form-field">
              <label>{t('messages.message')}</label>
              <textarea
                className="filter-input"
                rows={3}
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder={t('messages.messagePlaceholder')}
                style={{ width: '100%' }}
              />
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                className="btn btn-primary"
                onClick={handleCreate}
                disabled={creating || !newParticipant || !newMessage}
              >
                {creating ? t('app.loading') : t('messages.send')}
              </button>
              <button className="btn btn-secondary" onClick={() => setShowNew(false)}>
                {t('app.cancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
