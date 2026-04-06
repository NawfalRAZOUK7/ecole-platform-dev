import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ApiClientError, type ApiError } from '@/services/api/client';
import { wsClient, type WsEvent } from '@/services/ws/WebSocketClient';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { feedService } from './feed.service';
import { FeedItemCard } from './FeedItem';
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

function normalizeFeedItem(event: WsEvent): FeedItem | null {
  if (event.event !== 'feed_new') {
    return null;
  }

  const data = event.data;
  const id = typeof data.id === 'string' ? data.id : typeof data.reference_id === 'string' ? data.reference_id : null;
  const itemType = typeof data.item_type === 'string' ? data.item_type : typeof data.type === 'string' ? data.type : 'feed_new';
  const title = typeof data.title === 'string' ? data.title : null;

  if (!id || !title) {
    return null;
  }

  return {
    id,
    school_id: typeof data.school_id === 'string' ? data.school_id : null,
    item_type: itemType,
    title,
    summary: typeof data.summary === 'string' ? data.summary : typeof data.body === 'string' ? data.body : null,
    reference_type: typeof data.reference_type === 'string' ? data.reference_type : null,
    reference_id: typeof data.reference_id === 'string' ? data.reference_id : null,
    published_at: typeof data.published_at === 'string' ? data.published_at : new Date().toISOString(),
    action_url: typeof data.action_url === 'string' ? data.action_url : null,
    body: typeof data.body === 'string' ? data.body : null,
  };
}

function resolveFeedDestination(item: FeedItem) {
  if (item.action_url) {
    return item.action_url;
  }

  const source = `${item.item_type}:${item.reference_type || ''}`;
  if (source.includes('announcement')) {
    return '/announcements';
  }
  if (source.includes('grade')) {
    return '/results';
  }
  if (source.includes('attendance')) {
    return '/justification';
  }
  if (source.includes('invoice') || source.includes('payment')) {
    return '/invoices';
  }
  if (source.includes('message')) {
    return '/messages';
  }

  return '/feed';
}

export function FeedPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [dismissedError, setDismissedError] = useState(false);
  const [typeFilter, setTypeFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  const [readFilter, setReadFilter] = useState<'all' | 'read' | 'unread'>('all');
  const [realtimeItems, setRealtimeItems] = useState<FeedItem[]>([]);
  const [readVersion, setReadVersion] = useState(0);
  const loadMoreRef = useRef<HTMLDivElement | null>(null);
  const feedQuery = useFeed({
    type: typeFilter || undefined,
  });

  const queryItems = useMemo(
    () => feedQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [feedQuery.data]
  );
  const mergedItems = useMemo(() => {
    const seen = new Map<string, FeedItem>();
    [...realtimeItems, ...queryItems].forEach((item) => {
      if (!seen.has(item.id)) {
        seen.set(item.id, item);
      }
    });
    return Array.from(seen.values());
  }, [queryItems, realtimeItems]);
  const items = useMemo(
    () =>
      mergedItems.filter((item) => {
        const isRead = feedService.isRead(item.id);
        const matchesType = !typeFilter || item.item_type === typeFilter;
        const matchesDate = !dateFilter || item.published_at.slice(0, 10) >= dateFilter;
        const matchesRead =
          readFilter === 'all' ||
          (readFilter === 'read' && isRead) ||
          (readFilter === 'unread' && !isRead);

        return matchesType && matchesDate && matchesRead;
      }),
    [dateFilter, mergedItems, readFilter, readVersion, typeFilter]
  );
  const bannerError = useMemo(
    () => toBannerError(feedQuery.error, t('app.error')),
    [feedQuery.error, t]
  );

  useEffect(() => {
    setDismissedError(false);
  }, [bannerError]);

  useEffect(() => {
    return feedService.subscribeToReadChanges(() => {
      setReadVersion((current) => current + 1);
    });
  }, []);

  useEffect(() => {
    const unsubscribe = wsClient.subscribe((event) => {
      const nextItem = normalizeFeedItem(event);
      if (!nextItem) {
        return;
      }

      if (typeFilter && nextItem.item_type !== typeFilter) {
        return;
      }

      setRealtimeItems((current) => [nextItem, ...current.filter((item) => item.id !== nextItem.id)]);
    });

    return unsubscribe;
  }, [typeFilter]);

  useEffect(() => {
    const target = loadMoreRef.current;
    if (!target) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (entry?.isIntersecting && feedQuery.hasNextPage && !feedQuery.isFetchingNextPage) {
          void feedQuery.fetchNextPage();
        }
      },
      { rootMargin: '160px' }
    );

    observer.observe(target);
    return () => observer.disconnect();
  }, [
    feedQuery.fetchNextPage,
    feedQuery.hasNextPage,
    feedQuery.isFetchingNextPage,
  ]);

  async function handleMarkAsRead(feedItemId: string) {
    await feedService.markAsRead(feedItemId);
    setReadVersion((current) => current + 1);
  }

  async function handleOpenItem(item: FeedItem) {
    if (!feedService.isRead(item.id)) {
      await handleMarkAsRead(item.id);
    }

    navigate(resolveFeedDestination(item));
  }

  if (feedQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('feed.title')}</h1>
          <p className="page-subtitle">{t('feed.subtitle')}</p>
        </div>
        <div className="page-actions">
          <select
            className="filter-select"
            value={typeFilter}
            aria-label={t('feed.filterType')}
            onChange={(event) => setTypeFilter(event.target.value)}
          >
            <option value="">{t('feed.allTypes')}</option>
            <option value="announcement">{t('feed.types.announcement')}</option>
            <option value="grade_published">{t('feed.types.grade_published')}</option>
            <option value="attendance_alert">{t('feed.types.attendance_alert')}</option>
            <option value="payment">{t('feed.types.payment')}</option>
          </select>
          <input
            type="date"
            className="filter-input"
            aria-label={t('feed.filterDate')}
            value={dateFilter}
            onChange={(event) => setDateFilter(event.target.value)}
          />
          <select
            className="filter-select"
            value={readFilter}
            aria-label={t('feed.filterRead')}
            onChange={(event) => setReadFilter(event.target.value as 'all' | 'read' | 'unread')}
          >
            <option value="all">{t('feed.allStatuses')}</option>
            <option value="unread">{t('feed.unread')}</option>
            <option value="read">{t('feed.read')}</option>
          </select>
        </div>
      </div>

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
              <FeedItemCard
                key={item.id}
                item={item}
                isRead={feedService.isRead(item.id)}
                onOpen={handleOpenItem}
                onMarkAsRead={(itemId) => {
                  void handleMarkAsRead(itemId);
                }}
              />
            ))}
          </div>

          <div ref={loadMoreRef} style={{ height: 1 }} />

          {feedQuery.isFetchingNextPage ? (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>{t('app.loading')}</div>
          ) : null}
        </>
      )}
    </div>
  );
}
