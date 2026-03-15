/**
 * Activities page — activity browser.
 *
 * Reference: S-081 — Activities page
 * Calls GET /activities with cursor pagination. STD, TCH, ADM roles.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';

interface Activity {
  id: string;
  course_id: string;
  title: string;
  activity_type: string;
  difficulty: string | null;
  objective: string | null;
  config_json: Record<string, unknown> | null;
  created_at: string;
}

export function ActivitiesPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const fetchActivities = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;

      const resp = await api.list<Activity>('/activities', params);
      if (cursor) {
        setItems((prev) => [...prev, ...resp.data]);
      } else {
        setItems(resp.data);
      }
      setNextCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [t]);

  useEffect(() => {
    setLoading(true);
    fetchActivities().finally(() => setLoading(false));
  }, [fetchActivities]);

  async function handleLoadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    await fetchActivities(nextCursor);
    setLoadingMore(false);
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('activities.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchActivities()} />

      {items.length === 0 ? (
        <EmptyState message={t('activities.empty')} icon="🎯" />
      ) : (
        <>
          <div className="card-list">
            {items.map((activity) => (
              <div key={activity.id} className="card activity-card">
                <div className="activity-header">
                  <span className="activity-type-badge">{activity.activity_type}</span>
                  {activity.difficulty && (
                    <span className="activity-difficulty-badge">{activity.difficulty}</span>
                  )}
                </div>
                <h3 className="activity-title">{activity.title}</h3>
                {activity.objective && (
                  <p className="activity-objective">{activity.objective}</p>
                )}
              </div>
            ))}
          </div>

          {hasMore && (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                className="btn btn-secondary"
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
