/**
 * Sessions page — list active sessions with device info, revoke button.
 *
 * Reference: Phase 4C (from 2A) — Session management UI
 * Calls GET /auth/sessions and DELETE /auth/sessions/{id}.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';

interface SessionItem {
  id: string;
  source: string;
  user_agent: string | null;
  ip_address: string | null;
  device_name: string | null;
  created_at: string;
  last_active: string | null;
  is_current: boolean;
}

export function SessionsPage() {
  const { t } = useTranslation();
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revoking, setRevoking] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    try {
      const resp = await api.get<SessionItem[]>('/auth/sessions');
      setSessions(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchSessions().finally(() => setLoading(false));
  }, [fetchSessions]);

  async function handleRevoke(sessionId: string) {
    setRevoking(sessionId);
    try {
      await api.delete(`/auth/sessions/${sessionId}`);
      await fetchSessions();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    } finally {
      setRevoking(null);
    }
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('sessions.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchSessions} />

      {sessions.length === 0 ? (
        <EmptyState message={t('sessions.empty')} />
      ) : (
        <div className="card-list">
          {sessions.map((s) => (
            <div
              key={s.id}
              className="card"
              style={s.is_current ? { borderColor: 'var(--color-primary)', borderWidth: 2 } : undefined}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>
                    {s.device_name || s.source || t('sessions.unknownDevice')}
                    {s.is_current && (
                      <span className="status-badge status-published" style={{ marginInlineStart: 8 }}>
                        {t('sessions.current')}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                    {s.ip_address && <span>IP: {s.ip_address}</span>}
                    <span>{t('sessions.created')}: {new Date(s.created_at).toLocaleString()}</span>
                    {s.last_active && <span>{t('sessions.lastActive')}: {new Date(s.last_active).toLocaleString()}</span>}
                  </div>
                  {s.user_agent && (
                    <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 4, opacity: 0.7 }}>
                      {s.user_agent.length > 80 ? s.user_agent.slice(0, 80) + '...' : s.user_agent}
                    </div>
                  )}
                </div>
                {!s.is_current && (
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => handleRevoke(s.id)}
                    disabled={revoking === s.id}
                  >
                    {revoking === s.id ? t('app.loading') : t('sessions.revoke')}
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
