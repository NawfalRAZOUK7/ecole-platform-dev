/**
 * Feed page — parent news feed with cursor pagination.
 *
 * Reference: S-081 — Feed page
 * Calls GET /feed with cursor pagination. Parent role only.
 */

import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ApiClientError, type ApiError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';
import type { FeedItem } from './types';
import { useFeed } from './useFeed';

function toBannerError(error: unknown, fallback: string): ApiError | string | null {
  if (!error) {
    return null;
  }
  if (error instanceof ApiClientError) {
    return error.apiError;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

export function FeedPage() {
  const { t, i18n } = useTranslation();
  const feedQuery = useFeed();
  const [dismissedError, setDismissedError] = useState(false);

  const items: FeedItem[] = useMemo(
    () => feedQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [feedQuery.data]
  );
  const bannerError = useMemo(
    () => toBannerError(feedQuery.error, t('app.error')),
    [feedQuery.error, t]
  );

  useEffect(() => {
    setDismissedError(false);
  }, [bannerError]);

  if (feedQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <h1 className="page-title">{t('feed.title')}</h1>

      <ErrorBanner
        error={dismissedError ? null : bannerError}
        onDismiss={() => setDismissedError(true)}
        onRetry={() => void feedQuery.refetch()}
      />

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

          {feedQuery.hasNextPage && (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                className="btn btn-secondary"
                onClick={() => void feedQuery.fetchNextPage()}
                disabled={feedQuery.isFetchingNextPage}
              >
                {feedQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
