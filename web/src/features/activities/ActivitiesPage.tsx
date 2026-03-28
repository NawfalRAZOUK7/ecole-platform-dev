import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { EmptyState } from '@/shared/ui/EmptyState';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { toBannerError } from '@/shared/ui/errorUtils';
import { useActivities } from './useActivities';

export function ActivitiesPage() {
  const { t } = useTranslation();
  const activitiesQuery = useActivities();
  const items = useMemo(
    () => activitiesQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [activitiesQuery.data]
  );
  const errorState = useDismissibleError(toBannerError(activitiesQuery.error, t('app.error')));

  if (activitiesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('activities.title')}</h1>

      <ErrorBanner
        error={errorState.error}
        onDismiss={errorState.dismiss}
        onRetry={() => void activitiesQuery.refetch()}
      />

      {items.length === 0 ? (
        <EmptyState message={t('activities.empty')} icon="🎯" />
      ) : (
        <>
          <div className="card-list">
            {items.map((activity) => (
              <div key={activity.id} className="card activity-card">
                <div className="activity-header">
                  <span className="activity-type-badge">{activity.activity_type}</span>
                  {activity.difficulty ? (
                    <span className="activity-difficulty-badge">{activity.difficulty}</span>
                  ) : null}
                </div>
                <h3 className="activity-title">{activity.title}</h3>
                {activity.objective ? (
                  <p className="activity-objective">{activity.objective}</p>
                ) : null}
              </div>
            ))}
          </div>

          {activitiesQuery.hasNextPage ? (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                className="btn btn-secondary"
                onClick={() => void activitiesQuery.fetchNextPage()}
                disabled={activitiesQuery.isFetchingNextPage}
              >
                {activitiesQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
