import { useTranslation } from 'react-i18next';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useCmsAnalytics } from './useCms';

export function CmsAnalyticsPage() {
  const { t } = useTranslation();
  const analyticsQuery = useCmsAnalytics();

  if (analyticsQuery.isLoading) {
    return <LoadingState />;
  }

  const snapshot = analyticsQuery.data;
  if (!snapshot) {
    return (
      <div className="page">
        <ErrorBanner
          error={analyticsQuery.error instanceof Error ? analyticsQuery.error.message : t('cms.analytics.noData')}
          onRetry={() => void analyticsQuery.refetch()}
        />
      </div>
    );
  }

  const { contentStats, submissionStats, quizStats } = snapshot;

  return (
    <div className="page">
      <h1 className="page-title">{t('cms.analytics.title')}</h1>
      <ErrorBanner
        error={analyticsQuery.error instanceof Error ? analyticsQuery.error.message : null}
        onDismiss={() => {}}
        onRetry={() => void analyticsQuery.refetch()}
      />

      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', marginBottom: 16 }}>
        <StatCard label={t('cms.analytics.totalContent')} value={contentStats.total_items} />
        <StatCard label={t('cms.analytics.totalSubmissions')} value={submissionStats.total_submissions} />
        <StatCard label={t('cms.analytics.totalQuizzes')} value={quizStats.total_quizzes} />
        <StatCard
          label={t('cms.analytics.avgReviewTime')}
          value={submissionStats.avg_review_time_hours != null ? `${submissionStats.avg_review_time_hours}h` : '—'}
          accent
        />
      </div>

      <div className="card-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 12px' }}>{t('cms.analytics.byStatus')}</h3>
          {Object.entries(contentStats.by_status).map(([key, value]) => (
            <BarRow key={key} label={t(`cms.statuses.${key}`, key)} value={value} total={contentStats.total_items} />
          ))}
        </div>

        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 12px' }}>{t('cms.analytics.byOrigin')}</h3>
          {Object.entries(contentStats.by_origin).map(([key, value]) => (
            <BarRow key={key} label={t(`cms.origins.${key}`, key)} value={value} total={contentStats.total_items} />
          ))}
        </div>

        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 12px' }}>{t('cms.analytics.submissionStatus')}</h3>
          {Object.entries(submissionStats.by_status).map(([key, value]) => (
            <BarRow key={key} label={t(`cms.reviewStatuses.${key}`, key)} value={value} total={submissionStats.total_submissions} />
          ))}
          {submissionStats.total_submissions === 0 ? (
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('cms.analytics.noData')}</p>
          ) : null}
        </div>

        <div className="card" style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 12px' }}>{t('cms.analytics.topContributors')}</h3>
          {submissionStats.top_contributors.length > 0 ? (
            <table style={{ width: '100%', fontSize: 13 }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--color-border)' }}>
                  <th style={{ padding: '4px 0' }}>{t('cms.analytics.teacher')}</th>
                  <th style={{ padding: '4px 0', textAlign: 'right' }}>{t('cms.analytics.submissions')}</th>
                </tr>
              </thead>
              <tbody>
                {submissionStats.top_contributors.map((contributor, index) => (
                  <tr key={`${contributor.submitter_name}-${index}`} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '6px 0' }}>{contributor.submitter_name}</td>
                    <td style={{ padding: '6px 0', textAlign: 'right', fontWeight: 600 }}>{contributor.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ fontSize: 13, color: 'var(--color-text-secondary)' }}>{t('cms.analytics.noData')}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string | number; accent?: boolean }) {
  return (
    <div className="card" style={{ padding: 16, textAlign: 'center' }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: accent ? 'var(--color-warning)' : 'var(--color-primary)' }}>
        {value}
      </div>
      <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 4 }}>{label}</div>
    </div>
  );
}

function BarRow({ label, value, total }: { label: string; value: number; total: number }) {
  const percentage = total > 0 ? (value / total) * 100 : 0;

  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <div style={{ background: 'var(--color-border)', borderRadius: 999, height: 8, overflow: 'hidden' }}>
        <div
          style={{
            width: `${Math.min(percentage, 100)}%`,
            background: 'var(--color-primary)',
            height: '100%',
          }}
        />
      </div>
    </div>
  );
}
