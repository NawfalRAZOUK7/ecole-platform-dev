/**
 * Admin Dashboard — summary cards with key metrics.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Calls GET /admin/dashboard. ADM and DIR roles.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';

interface DashboardData {
  users: number;
  active_sessions: number;
  active_invitations: number;
  audit_events_24h: number;
  pending_justifications: number;
  users_by_role: Record<string, number>;
}

export function DashboardPage() {
  const { t } = useTranslation();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      const resp = await api.get<DashboardData>('/admin/dashboard');
      setData(resp.data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchDashboard().finally(() => setLoading(false));
  }, [fetchDashboard]);

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.dashboard.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={fetchDashboard} />

      {data && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{data.users}</div>
              <div className="stat-label">{t('admin.dashboard.users')}</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.active_sessions}</div>
              <div className="stat-label">{t('admin.dashboard.sessions')}</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.active_invitations}</div>
              <div className="stat-label">{t('admin.dashboard.invitations')}</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.audit_events_24h}</div>
              <div className="stat-label">{t('admin.dashboard.auditEvents')}</div>
            </div>
            <div className="stat-card stat-card--warning">
              <div className="stat-value">{data.pending_justifications}</div>
              <div className="stat-label">{t('admin.dashboard.pendingJustifications')}</div>
            </div>
          </div>

          {Object.keys(data.users_by_role).length > 0 && (
            <div className="card" style={{ marginTop: 24 }}>
              <h3 style={{ marginBottom: 12, fontSize: 16, fontWeight: 600 }}>
                {t('admin.dashboard.usersByRole')}
              </h3>
              <div className="role-breakdown">
                {Object.entries(data.users_by_role).map(([role, count]) => (
                  <div key={role} className="role-breakdown-item">
                    <span className="role-badge">{t(`roles.${role}`, role)}</span>
                    <span className="role-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
