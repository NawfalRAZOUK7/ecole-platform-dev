/**
 * ReviewDetailPage — Parent views a specific child session and adds comments.
 *
 * Phase B1: Interface de révision partagée parent-enfant.
 * Shows session detail (quiz result, content progress, writing feedback) and
 * a comment section for parent encouragements.
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { sharedReviewService } from './sharedReview.service';

const ENCOURAGEMENT_EMOJIS = ['👏', '🌟', '💪', '❤️', '🎉', '🏆'];

export function ReviewDetailPage() {
  const { t } = useTranslation();
  const { childId, sessionId } = useParams<{ childId: string; sessionId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [commentText, setCommentText] = useState('');
  const [selectedEmoji, setSelectedEmoji] = useState<string | null>(null);

  const detailQuery = useQuery({
    queryKey: ['shared-review', childId, 'sessions', sessionId],
    queryFn: () => sharedReviewService.getSessionDetail(childId!, sessionId!),
    enabled: !!childId && !!sessionId,
  });

  const commentMutation = useMutation({
    mutationFn: () =>
      sharedReviewService.addComment(childId!, sessionId!, {
        text: commentText,
        emoji: selectedEmoji ?? undefined,
      }),
    onSuccess: () => {
      setCommentText('');
      setSelectedEmoji(null);
      queryClient.invalidateQueries({
        queryKey: ['shared-review', childId, 'sessions', sessionId],
      });
    },
  });

  if (detailQuery.isLoading) return <LoadingState />;
  if (detailQuery.isError) {
    return <ErrorBanner message={t('errors.generic', 'Something went wrong.')} />;
  }

  const session = detailQuery.data!;
  const canSubmitComment = commentText.trim().length > 0 && !commentMutation.isPending;

  return (
    <div className="page">
      {/* Back link */}
      <button
        type="button"
        onClick={() => navigate(`/family/review/${childId}`)}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--color-primary)',
          cursor: 'pointer',
          fontSize: '0.9rem',
          padding: 0,
          marginBottom: 16,
          display: 'inline-flex',
          alignItems: 'center',
          gap: 4,
        }}
      >
        ← {t('sharedReview.backToSessions', 'Back to sessions')}
      </button>

      <h1 className="page-title">{session.title}</h1>

      {/* Session info card */}
      <div className="card" style={{ padding: 20, marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
          <InfoItem label={t('sharedReview.type', 'Type')} value={session.type} />
          <InfoItem label={t('sharedReview.status', 'Status')} value={session.status} />
          {session.score != null && (
            <InfoItem
              label={t('sharedReview.score', 'Score')}
              value={`${session.score}${session.max_score ? `/${session.max_score}` : '/100'}`}
            />
          )}
          {session.started_at && (
            <InfoItem
              label={t('sharedReview.date', 'Date')}
              value={new Date(session.started_at).toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            />
          )}
        </div>
      </div>

      {/* Writing-specific: show text + suggestion */}
      {session.type === 'writing' && session.text && (
        <div className="card" style={{ padding: 20, marginBottom: 16 }}>
          <h3
            style={{
              fontSize: '1rem',
              fontWeight: 700,
              margin: '0 0 12px',
              color: 'var(--color-primary)',
            }}
          >
            {t('sharedReview.childText', "Child's text")}
          </h3>
          <div
            style={{
              padding: 14,
              background: 'var(--color-bg-secondary, #f9fafb)',
              borderRadius: 10,
              fontSize: '0.95rem',
              lineHeight: 1.7,
              direction: 'rtl',
              whiteSpace: 'pre-wrap',
            }}
          >
            {session.text}
          </div>
          {session.suggestion && (
            <>
              <h3
                style={{
                  fontSize: '1rem',
                  fontWeight: 700,
                  margin: '16px 0 12px',
                  color: 'var(--color-success)',
                }}
              >
                {t('sharedReview.aiSuggestion', 'AI Suggestion')}
              </h3>
              <div
                style={{
                  padding: 14,
                  background: 'var(--color-surface-success, #ecfdf5)',
                  borderRadius: 10,
                  fontSize: '0.95rem',
                  lineHeight: 1.7,
                  direction: 'rtl',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {session.suggestion}
              </div>
            </>
          )}
        </div>
      )}

      {/* Comments section */}
      <div className="card" style={{ padding: 20 }}>
        <h3
          style={{
            fontSize: '1rem',
            fontWeight: 700,
            margin: '0 0 16px',
            color: 'var(--color-primary)',
          }}
        >
          {t('sharedReview.comments', 'Encouragements')}
          {session.comments.length > 0 && (
            <span
              style={{
                fontSize: '0.8rem',
                fontWeight: 500,
                color: 'var(--color-text-secondary)',
                marginLeft: 8,
              }}
            >
              ({session.comments.length})
            </span>
          )}
        </h3>

        {/* Existing comments */}
        {session.comments.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
            {session.comments.map((c) => (
              <div
                key={c.id}
                style={{
                  padding: '10px 14px',
                  background: 'var(--color-bg-secondary, #f9fafb)',
                  borderRadius: 12,
                  fontSize: '0.9rem',
                  lineHeight: 1.5,
                }}
              >
                {c.emoji && <span style={{ fontSize: '1.2rem', marginRight: 6 }}>{c.emoji}</span>}
                {c.text}
                <div
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--color-text-secondary)',
                    marginTop: 4,
                  }}
                >
                  {new Date(c.created_at).toLocaleDateString('fr-FR', {
                    day: 'numeric',
                    month: 'short',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p
            style={{
              fontSize: '0.85rem',
              color: 'var(--color-text-secondary)',
              margin: '0 0 16px',
            }}
          >
            {t('sharedReview.noComments', 'No comments yet. Be the first to encourage!')}
          </p>
        )}

        {/* Add comment form */}
        <div>
          {/* Emoji picker */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 10, flexWrap: 'wrap' }}>
            {ENCOURAGEMENT_EMOJIS.map((emoji) => (
              <button
                key={emoji}
                type="button"
                onClick={() => setSelectedEmoji(selectedEmoji === emoji ? null : emoji)}
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  border:
                    selectedEmoji === emoji
                      ? '2px solid var(--color-primary)'
                      : '2px solid var(--color-border)',
                  background:
                    selectedEmoji === emoji
                      ? 'var(--color-surface-primary, #f3e8ff)'
                      : 'var(--color-surface)',
                  fontSize: '1.1rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {emoji}
              </button>
            ))}
          </div>

          {/* Text input */}
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder={t('sharedReview.commentPlaceholder', 'Write an encouragement...')}
              maxLength={1000}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && canSubmitComment) {
                  commentMutation.mutate();
                }
              }}
              style={{
                flex: 1,
                padding: '10px 14px',
                borderRadius: 12,
                border: '2px solid var(--color-border)',
                fontSize: '0.9rem',
                outline: 'none',
                background: 'var(--color-surface)',
                color: 'var(--color-text)',
              }}
            />
            <button
              type="button"
              onClick={() => commentMutation.mutate()}
              disabled={!canSubmitComment}
              style={{
                padding: '10px 18px',
                borderRadius: 12,
                border: 'none',
                background: canSubmitComment ? 'var(--color-primary)' : 'var(--color-border)',
                color: '#fff',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: canSubmitComment ? 'pointer' : 'not-allowed',
              }}
            >
              {commentMutation.isPending ? '...' : t('sharedReview.send', 'Send')}
            </button>
          </div>

          {commentMutation.isError && (
            <p
              style={{
                fontSize: '0.8rem',
                color: 'var(--color-error)',
                marginTop: 8,
              }}
            >
              {t('errors.generic', 'Something went wrong.')}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ minWidth: 100 }}>
      <div
        style={{
          fontSize: '0.75rem',
          fontWeight: 600,
          color: 'var(--color-text-secondary)',
          textTransform: 'uppercase',
          marginBottom: 2,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: '0.95rem',
          fontWeight: 600,
          color: 'var(--color-text)',
          textTransform: 'capitalize',
        }}
      >
        {value}
      </div>
    </div>
  );
}
