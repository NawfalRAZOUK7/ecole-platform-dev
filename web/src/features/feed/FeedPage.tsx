/**
 * Feed page — parent news feed with cursor pagination.
 *
 * Reference: S-081 — Feed page
 * Calls GET /feed with cursor pagination. Parent role only.
 */

import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';

interface FeedItem {
  id: string;
  school_id: string;
  item_type: string;
  title: string;
  summary: string | null;
  reference_type: string | null;
  reference_id: string | null;
  published_at: string;
}

export function FeedPage() {
  const { t, i18n } = useTranslation();
  const [items, setItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  const fetchFeed = useCallback(async (cursor?: string) => {
    try {
      const params: Record<string, string | number | undefined> = {};
      if (cursor) params.cursor = cursor;

      const resp = await api.list<FeedItem>('/feed', params);
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
    fetchFeed().finally(() => setLoading(false));
  }, [fetchFeed]);

  async function handleLoadMore() {
    if (!nextCursor) return;
    setLoadingMore(true);
    await fetchFeed(nextCursor);
    setLoadingMore(false);
  }

  if (loading) return <LoadingState />;

  return (
    <div className="page">
      <h1 className="page-title">{t('feed.title')}</h1>

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => fetchFeed()} />

      {items.length === 0 ? (
        <EmptyState message={t('feed.empty')} icon="📰" />
      ) : (
        <>
          <div className="feed-list">
            {items.map((item) => (
              <article key={item.id} className="card feed-item">
                <div className="feed-item-header">
                  <span className="feed-type-badge">{item.item_type}</span>
                  <time className="feed-date">{formatDate(item.published_at, i18n.language)}</time>
                </div>
                <h3 className="feed-title">{item.title}</h3>
                {item.summary && <p className="feed-summary">{item.summary}</p>}
              </article>
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
