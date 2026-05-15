/**
 * SharedReviewPage — Parent views child's recent learning sessions.
 *
 * Phase B1: Interface de révision partagée parent-enfant.
 * Shows a unified feed of quiz attempts, content progress, writing attempts,
 * and activity sessions for a specific child.
 */

import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { LoadingState } from '@/shared/ui/LoadingState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { sharedReviewService } from '../api/sharedReview.api';
import type { ReviewSession } from '../api/sharedReview.api';

const TYPE_ICONS: Record<string, string> = {
  quiz: '📝',
  content: '📖',
  writing: '✏️',
  activity: '🎮',
};

const TYPE_COLORS: Record<string, string> = {
  quiz: 'var(--color-primary)',
  content: 'var(--color-info)',
  writing: 'var(--color-success)',
  activity: 'var(--color-warning)',
};

function scoreColor(score: number | null | undefined): string {
  if (score == null) return 'var(--color-text-secondary)';
  if (score >= 80) return 'var(--color-success)';
  if (score >= 50) return 'var(--color-warning)';
  return 'var(--color-error)';
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function SharedReviewPage() {
  const { t } = useTranslation();
  const { childId } = useParams<{ childId: string }>();
  const navigate = useNavigate();

  const sessionsQuery = useQuery({
    queryKey: ['shared-review', childId, 'sessions'],
    queryFn: () => sharedReviewService.listSessions(childId!, { limit: 50 }),
    enabled: !!childId,
  });

  if (sessionsQuery.isLoading) return <LoadingState />;
  if (sessionsQuery.isError) {
    return <ErrorBanner error={t('errors.generic', 'Something went wrong.')} />;
  }

  const data = sessionsQuery.data;
  const sessions = data?.sessions ?? [];

  return (
    <div className="page">
      <h1 className="page-title">{t('sharedReview.title', "Child's learning sessions")}</h1>
      <p className="page-subtitle">
        {t('sharedReview.subtitle', 'Review recent activities and add encouragements')}
      </p>

      {sessions.length === 0 ? (
        <div
          className="card"
          style={{ padding: 32, textAlign: 'center', color: 'var(--color-text-secondary)' }}
        >
          <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>📭</div>
          <p>{t('sharedReview.noSessions', 'No learning sessions yet.')}</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {sessions.map((session) => (
            <SessionCard
              key={session.id}
              session={session}
              onClick={() => navigate(`/family/review/${childId}/sessions/${session.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SessionCard({ session, onClick }: { session: ReviewSession; onClick: () => void }) {
  const { t } = useTranslation();

  return (
    <button
      type="button"
      className="card"
      onClick={onClick}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '14px 18px',
        cursor: 'pointer',
        textAlign: 'left',
        width: '100%',
        border: '1px solid var(--color-border)',
        background: 'var(--color-surface)',
        transition: 'box-shadow 0.15s ease',
      }}
    >
      {/* Type icon */}
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: 12,
          background: `${TYPE_COLORS[session.type] || 'var(--color-primary)'}15`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.4rem',
          flexShrink: 0,
        }}
      >
        {TYPE_ICONS[session.type] || '📋'}
      </div>

      {/* Info */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontWeight: 600,
            fontSize: '0.95rem',
            color: 'var(--color-text)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {session.title}
        </div>
        <div
          style={{
            fontSize: '0.8rem',
            color: 'var(--color-text-secondary)',
            marginTop: 2,
          }}
        >
          {formatDate(session.started_at)}
          {session.status === 'completed' && (
            <span style={{ marginLeft: 8, color: 'var(--color-success)' }}>✓</span>
          )}
        </div>
      </div>

      {/* Score badge */}
      {session.score != null && (
        <div
          style={{
            fontWeight: 700,
            fontSize: '1rem',
            color: scoreColor(session.score),
            flexShrink: 0,
          }}
        >
          {session.score}
          {session.max_score ? `/${session.max_score}` : '%'}
        </div>
      )}

      {/* Type badge */}
      <span
        style={{
          fontSize: '0.7rem',
          fontWeight: 600,
          padding: '3px 8px',
          borderRadius: 8,
          background: `${TYPE_COLORS[session.type] || 'var(--color-primary)'}15`,
          color: TYPE_COLORS[session.type] || 'var(--color-primary)',
          textTransform: 'capitalize',
          flexShrink: 0,
        }}
      >
        {t(`sharedReview.types.${session.type}`, session.type)}
      </span>
    </button>
  );
}
