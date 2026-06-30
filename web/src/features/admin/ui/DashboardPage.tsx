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
import { StatGridSkeleton } from '@/shared/ui/SkeletonLayouts';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useAdminDashboard } from '@/features/admin/model/useAdmin';
import { useCountUp } from '@/shared/hooks/useCountUp';

/** Animated KPI used inside the dashboard hero. */
function HeroKpi({ value, label }: { value: number; label: string }) {
  const display = useCountUp(value);
  return (
    <div className="dashboard-hero__kpi">
      <span className="dashboard-hero__kpi-value">{Math.round(display).toLocaleString()}</span>
      <span className="dashboard-hero__kpi-label">{label}</span>
    </div>
  );
}

export function DashboardPage() {
  const { t } = useTranslation();
  const dashboardQuery = useAdminDashboard();
  const bannerError = useMemo(
    () => toBannerError(dashboardQuery.error, t('app.error')),
    [dashboardQuery.error, t],
  );
  const dismissibleError = useDismissibleError(bannerError);
  const data = dashboardQuery.data;
  const rewardsSummary = data?.rewards_summary;

  if (dashboardQuery.isLoading) {
    return <StatGridSkeleton />;
  }

  return (
    <div className="page">
      <ErrorBanner
        error={dismissibleError.error}
        onDismiss={dismissibleError.dismiss}
        onRetry={() => void dashboardQuery.refetch()}
      />

      {data && (
        <>
          <section className="dashboard-hero">
            <div className="dashboard-hero__glow" aria-hidden="true" />
            <div className="dashboard-hero__text">
              <p className="dashboard-hero__eyebrow">{t('admin.dashboard.title')}</p>
              <h1 className="dashboard-hero__greeting">
                {t('admin.dashboard.heroGreeting', 'Tableau de bord')}
              </h1>
              <p className="dashboard-hero__sub">
                {t('admin.dashboard.heroSubtitle', "Aperçu de l'activité de votre établissement.")}
              </p>
            </div>
            <div className="dashboard-hero__kpis">
              <HeroKpi value={data.users} label={t('admin.dashboard.users')} />
              <HeroKpi value={data.active_sessions} label={t('admin.dashboard.sessions')} />
              <HeroKpi
                value={data.pending_justifications}
                label={t('admin.dashboard.pendingJustifications')}
              />
            </div>
          </section>

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
                <div className="stat-value">{rewardsSummary?.stars_awarded_week ?? 0}</div>
                <div className="stat-label">{t('admin.dashboard.starsAwardedWeek')}</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{rewardsSummary?.stars_awarded_month ?? 0}</div>
                <div className="stat-label">{t('admin.dashboard.starsAwardedMonth')}</div>
              </div>
              <div className="stat-card">
                <div className="stat-value" style={{ fontSize: 20 }}>
                  {rewardsSummary?.most_active_class ?? '—'}
                </div>
                <div className="stat-label">{t('admin.dashboard.mostActiveClass')}</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{rewardsSummary?.recent_reward_events ?? 0}</div>
                <div className="stat-label">{t('admin.dashboard.recentBadgeUnlocks')}</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
