/**
 * Notifications page — list of user notifications with cursor pagination.
 *
 * Reference: S-081 — Notifications page
 * Calls GET /notifications. Available to PAR, TCH, ADM roles.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface Notification {
  id: string;
  user_id: string;
  channel: string;
  subject: string;
  body_plain: string | null;
  body_html: string | null;
  sent_at: string | null;
  created_at: string;
}

export function NotificationsPage() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const fetchNotifications = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;

      const resp = await api.list<Notification>('/notifications', params);
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
    fetchNotifications().finally(() => setLoading(false));
  }, [fetchNotifications]);

  async function handleLoadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    await fetchNotifications(nextCursor);
    setLoadingMore(false);
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('notifications.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchNotifications()} />

      {items.length === 0 ? (
        <EmptyState message={t('notifications.empty')} icon="🔔" />
      ) : (
        <>
          <div className="card-list">
            {items.map((notif) => (
              <div key={notif.id} className="card notification-card">
                <div className="notification-header">
                  <span className="notification-channel">{notif.channel}</span>
                  <time className="notification-date">
                    {formatDate(notif.sent_at || notif.created_at, i18n.language)}
                  </time>
                </div>
                <h3 className="notification-subject">{notif.subject}</h3>
                {notif.body_plain && (
                  <p className="notification-body">{notif.body_plain}</p>
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
