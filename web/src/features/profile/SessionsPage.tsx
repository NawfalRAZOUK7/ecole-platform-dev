/**
 * Sessions page — list active sessions with device info, revoke button.
 *
 * Reference: Phase 4C (from 2A) — Session management UI
 * Calls GET /auth/sessions and DELETE /auth/sessions/{id}.
 */

import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useRevokeSession, useSessions } from './useProfile';
import type { SessionItem } from './profile.service';

export function SessionsPage() {
  const { t } = useTranslation();
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const sessionsQuery = useSessions();
  const revokeMutation = useRevokeSession();
  const sessions: SessionItem[] = useMemo(() => sessionsQuery.data ?? [], [sessionsQuery.data]);
  const dismissibleError = useDismissibleError(
    toBannerError(sessionsQuery.error ?? revokeMutation.error, t('app.error'))
  );

  async function handleRevoke(sessionId: string) {
    setRevokingId(sessionId);
    await revokeMutation.mutateAsync(sessionId);
    await sessionsQuery.refetch();
    setRevokingId(null);
  }

  if (sessionsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('sessions.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void sessionsQuery.refetch()}
      />

      {sessions.length === 0 ? (
        <EmptyState message={t('sessions.empty')} />
      ) : (
        <div className="card-list">
          {sessions.map((session) => (
            <div
              key={session.id}
              className="card"
              style={session.is_current ? { borderColor: 'var(--color-primary)', borderWidth: 2 } : undefined}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>
                    {session.device_name || session.source || t('sessions.unknownDevice')}
                    {session.is_current && (
                      <span className="status-badge status-published" style={{ marginInlineStart: 8 }}>
                        {t('sessions.current')}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                    {session.ip_address && <span>IP: {session.ip_address}</span>}
                    <span>{t('sessions.created')}: {new Date(session.created_at).toLocaleString()}</span>
                    {session.last_active && <span>{t('sessions.lastActive')}: {new Date(session.last_active).toLocaleString()}</span>}
                  </div>
                  {session.user_agent && (
                    <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 4, opacity: 0.7 }}>
                      {session.user_agent.length > 80 ? `${session.user_agent.slice(0, 80)}...` : session.user_agent}
                    </div>
                  )}
                </div>
                {!session.is_current && (
                  <button className="btn btn-danger btn-sm" onClick={() => void handleRevoke(session.id)} disabled={revokingId === session.id}>
                    {revokingId === session.id ? t('app.loading') : t('sessions.revoke')}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
