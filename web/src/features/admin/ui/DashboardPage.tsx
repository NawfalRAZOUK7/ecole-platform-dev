/**
 * Admin Dashboard — summary cards with key metrics.
 *
 * Reference: Phase 4A — Admin Dashboard
 * Calls GET /admin/dashboard. ADM and DIR roles.
 */

import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useAdminDashboard } from '@/features/admin/model/useAdmin';

export function DashboardPage() {
  const { t } = useTranslation();
  const dashboardQuery = useAdminDashboard();
  const bannerError = useMemo(
    () => toBannerError(dashboardQuery.error, t('app.error')),
    [dashboardQuery.error, t],
  );
  const dismissibleError = useDismissibleError(bannerError);
  const data = dashboardQuery.data;

  if (dashboardQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('admin.dashboard.title')}</h1>

      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void dashboardQuery.refetch()}
      />

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

          <div className="card" style={{ marginTop: 24 }}>
            <div style={{ marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600 }}>
                {t('admin.dashboard.gamificationTitle')}
              </h3>
              <p style={{ margin: '6px 0 0', color: 'var(--color-text-secondary)' }}>
                {t('admin.dashboard.gamificationSubtitle')}
              </p>
            </div>

            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">N/A</div>
                <div className="stat-label">{t('admin.dashboard.starsAwardedWeek')}</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">N/A</div>
                <div className="stat-label">{t('admin.dashboard.starsAwardedMonth')}</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">N/A</div>
                <div className="stat-label">{t('admin.dashboard.mostActiveClass')}</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">N/A</div>
                <div className="stat-label">{t('admin.dashboard.recentBadgeUnlocks')}</div>
              </div>
            </div>

            <p style={{ margin: '16px 0 0', color: 'var(--color-text-secondary)' }}>
              {t('admin.dashboard.gamificationUnavailable')}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
