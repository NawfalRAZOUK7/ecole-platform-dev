/**
 * Conversations page — inbox-style list of conversations.
 *
 * Reference: Phase 12A — Messaging UI
 * Calls GET /messages/conversations (cursor-paginated).
 * "New Message" button starts a new conversation via POST /messages/conversations.
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/app/providers/AuthContext';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { formatDate } from '@/shared/i18n';
import { useConversations, useCreateConversation } from '../model/useMessages';
import type { Conversation } from '../api/messages.api';

export function ConversationsPage() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [showNew, setShowNew] = useState(false);
  const [newParticipant, setNewParticipant] = useState('');
  const [newSubject, setNewSubject] = useState('');
  const [newMessage, setNewMessage] = useState('');
  const conversationsQuery = useConversations();
  const createConversationMutation = useCreateConversation();
  const items: Conversation[] = useMemo(
    () => conversationsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [conversationsQuery.data],
  );
  const dismissibleError = useDismissibleError(
    toBannerError(conversationsQuery.error ?? createConversationMutation.error, t('app.error')),
  );

  async function handleCreate() {
    const conversation = await createConversationMutation.mutateAsync({
      type: 'DIRECT',
      participant_ids: [newParticipant],
      subject: newSubject || undefined,
      initial_message: newMessage,
    });
    setShowNew(false);
    setNewParticipant('');
    setNewSubject('');
    setNewMessage('');
    navigate(`/messages/${conversation.id}`);
  }

  function getOtherParticipant(conversation: Conversation): string {
    const other = conversation.participants.find((participant) => participant.user_id !== user?.id);
    if (other) {
      return `${other.user_id.slice(0, 8)}...`;
    }
    return conversation.subject || t('messages.conversation');
  }

  if (conversationsQuery.isLoading && !conversationsQuery.data) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <h1 className="page-title" style={{ marginBottom: 0 }}>
          {t('messages.title')}
        </h1>
        <button className="btn btn-primary" onClick={() => setShowNew(true)}>
          + {t('messages.newConversation')}
        </button>
      </div>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void conversationsQuery.refetch()}
      />

      {items.length === 0 ? (
        <EmptyState message={t('messages.empty')} icon="💬" />
      ) : (
        <div className="card-list">
          {items.map((conversation) => (
            <div
              key={conversation.id}
              className="card conversation-card"
              onClick={() => navigate(`/messages/${conversation.id}`)}
              style={{ cursor: 'pointer' }}
            >
              <div
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span
                      style={{
                        fontWeight: conversation.unread_count > 0 ? 700 : 600,
                        fontSize: 15,
                      }}
                    >
                      {conversation.subject || getOtherParticipant(conversation)}
                    </span>
                    {conversation.unread_count > 0 && (
                      <span className="notif-badge">{conversation.unread_count}</span>
                    )}
                  </div>
                  {conversation.last_message_body && (
                    <div
                      style={{
                        fontSize: 13,
                        color: 'var(--color-text-secondary)',
                        marginTop: 2,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        maxWidth: 400,
                      }}
                    >
                      {conversation.last_message_body.length > 60
                        ? `${conversation.last_message_body.slice(0, 60)}...`
                        : conversation.last_message_body}
                    </div>
                  )}
                  <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 2 }}>
                    {conversation.type === 'DIRECT' ? t('messages.direct') : t('messages.group')}
                    {' · '}
                    {conversation.participants.length} {t('messages.participants')}
                  </div>
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>
                  {conversation.last_message_at
                    ? formatDate(conversation.last_message_at, i18n.language)
                    : formatDate(conversation.created_at, i18n.language)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {conversationsQuery.hasNextPage && (
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <button
            className="btn btn-secondary"
            onClick={() => void conversationsQuery.fetchNextPage()}
            disabled={conversationsQuery.isFetchingNextPage}
          >
            {conversationsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
          </button>
        </div>
      )}

      {showNew && (
        <div className="modal-overlay" onClick={() => setShowNew(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <h2 style={{ marginBottom: 16 }}>{t('messages.newConversation')}</h2>
            <div className="form-field">
              <label>{t('messages.recipient')}</label>
              <input
                type="text"
                value={newParticipant}
                onChange={(event) => setNewParticipant(event.target.value)}
                placeholder={t('messages.recipientPlaceholder')}
              />
            </div>
            <div className="form-field">
              <label>{t('messages.subject')}</label>
              <input
                type="text"
                value={newSubject}
                onChange={(event) => setNewSubject(event.target.value)}
                placeholder={t('messages.subjectPlaceholder')}
              />
            </div>
            <div className="form-field">
              <label>{t('messages.message')}</label>
              <textarea
                className="filter-input"
                rows={3}
                value={newMessage}
                onChange={(event) => setNewMessage(event.target.value)}
                placeholder={t('messages.messagePlaceholder')}
                style={{ width: '100%' }}
              />
            </div>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <button
                className="btn btn-primary"
                onClick={() => void handleCreate()}
                disabled={createConversationMutation.isPending || !newParticipant || !newMessage}
              >
                {createConversationMutation.isPending ? t('app.loading') : t('messages.send')}
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
