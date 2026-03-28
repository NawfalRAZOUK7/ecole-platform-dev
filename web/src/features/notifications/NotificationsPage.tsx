import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ApiClientError, type ApiError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';
import { useMarkAllNotificationsRead, useMarkNotificationRead, useNotifications } from './useNotifications';
import type { NotificationItem } from './types';

const CATEGORY_OPTIONS = ['academic', 'billing', 'attendance', 'system', 'announcement'] as const;
const CHANNEL_OPTIONS = ['in_app', 'push', 'email', 'sms'] as const;

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

export function NotificationsPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const [category, setCategory] = useState('');
  const [channel, setChannel] = useState('');
  const [readFilter, setReadFilter] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [dismissedError, setDismissedError] = useState(false);

  const queryFilters = useMemo(
    () => ({
      limit: 20,
      category: category || undefined,
      channel: channel || undefined,
      read: readFilter === '' ? undefined : readFilter,
      from: fromDate || undefined,
      to: toDate || undefined,
    }),
    [category, channel, fromDate, readFilter, toDate]
  );

  const notificationsQuery = useNotifications(queryFilters);
  const markReadMutation = useMarkNotificationRead();
  const markAllReadMutation = useMarkAllNotificationsRead();

  const items = useMemo(
    () => notificationsQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [notificationsQuery.data]
  );
  const bannerError = useMemo(
    () =>
      toBannerError(
        notificationsQuery.error ?? markReadMutation.error ?? markAllReadMutation.error,
        t('app.error')
      ),
    [markAllReadMutation.error, markReadMutation.error, notificationsQuery.error, t]
  );

  useEffect(() => {
    setDismissedError(false);
  }, [bannerError]);

  useEffect(() => {
    if (
      !notificationsQuery.hasNextPage ||
      notificationsQuery.isLoading ||
      notificationsQuery.isFetchingNextPage ||
      !sentinelRef.current
    ) {
      return undefined;
    }

    const observer = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting) {
        void notificationsQuery.fetchNextPage();
      }
    }, { threshold: 0.2 });

    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [
    notificationsQuery.fetchNextPage,
    notificationsQuery.hasNextPage,
    notificationsQuery.isFetchingNextPage,
    notificationsQuery.isLoading,
  ]);

  async function handleMarkRead(notification: NotificationItem, read = true) {
    await markReadMutation.mutateAsync({ id: notification.id, read });
  }

  async function handleMarkAllRead() {
    await markAllReadMutation.mutateAsync();
  }

  async function handleNotificationClick(notification: NotificationItem) {
    if (!notification.is_read) {
      await handleMarkRead(notification, true);
    }
    navigate(notification.action_url || '/notifications');
  }

  function resetFilters() {
    setCategory('');
    setChannel('');
    setReadFilter('');
    setFromDate('');
    setToDate('');
  }

  if (notificationsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('notifications.title')}</h1>
          <p className="page-subtitle">{t('notifications.subtitle')}</p>
        </div>
        <div className="page-actions">
          <button className="btn btn-secondary" onClick={resetFilters}>
            {t('notifications.clearFilters')}
          </button>
          <button className="btn btn-primary" onClick={() => void handleMarkAllRead()}>
            {t('notifications.markAllRead')}
          </button>
        </div>
      </div>

      <div className="filters-bar filters-bar--notifications">
        <select className="filter-select" value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">{t('notifications.filters.allCategories')}</option>
          {CATEGORY_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {t(`notifications.categories.${option}`)}
            </option>
          ))}
        </select>

        <select className="filter-select" value={channel} onChange={(e) => setChannel(e.target.value)}>
          <option value="">{t('notifications.filters.allChannels')}</option>
          {CHANNEL_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {t(`notifications.channels.${option}`)}
            </option>
          ))}
        </select>

        <select className="filter-select" value={readFilter} onChange={(e) => setReadFilter(e.target.value)}>
          <option value="">{t('notifications.filters.allStates')}</option>
          <option value="false">{t('notifications.filters.unread')}</option>
          <option value="true">{t('notifications.filters.read')}</option>
        </select>

        <input
          type="date"
          className="filter-input"
          value={fromDate}
          onChange={(e) => setFromDate(e.target.value)}
          aria-label={t('notifications.filters.from')}
        />

        <input
          type="date"
          className="filter-input"
          value={toDate}
          onChange={(e) => setToDate(e.target.value)}
          aria-label={t('notifications.filters.to')}
        />
      </div>

      <ErrorBanner
        error={dismissedError ? null : bannerError}
        onDismiss={() => setDismissedError(true)}
        onRetry={() => void notificationsQuery.refetch()}
      />

      {items.length === 0 ? (
        <EmptyState message={t('notifications.empty')} icon="🔔" />
      ) : (
        <div className="card-list">
          {items.map((notification) => (
            <article
              key={notification.id}
              className={`card notification-card ${notification.is_read ? 'notification-card--read' : 'notification-card--unread'}`}
            >
              <button
                type="button"
                className="notification-card__click"
                onClick={() => void handleNotificationClick(notification)}
              >
                <div className="notification-header">
                  <span className="notification-category-badge">
                    {t(`notifications.categories.${notification.category}`)}
                  </span>
                  <time className="notification-date">
                    {formatDate(notification.created_at, i18n.language, {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    })}
                  </time>
                </div>
                <div className="notification-card__meta">
                  <span className={`priority-badge priority-badge--${notification.priority}`}>
                    {t(`notifications.priorities.${notification.priority}`)}
                  </span>
                  <span className="notification-channel-list">
                    {notification.channels.map((item) => t(`notifications.channels.${item}`)).join(' • ')}
                  </span>
                </div>
                <h3 className="notification-subject">{notification.title}</h3>
                {notification.body && <p className="notification-body">{notification.body}</p>}
              </button>
              <div className="notification-card__actions">
                {!notification.is_read ? (
                  <button className="btn btn-secondary" onClick={() => void handleMarkRead(notification, true)}>
                    {t('notifications.markRead')}
                  </button>
                ) : (
                  <button className="btn btn-secondary" onClick={() => void handleMarkRead(notification, false)}>
                    {t('notifications.markUnread')}
                  </button>
                )}
                <button className="btn btn-secondary" onClick={() => navigate('/settings/notifications')}>
                  {t('notifications.manageSettings')}
                </button>
              </div>
            </article>
          ))}

          <div ref={sentinelRef} className="notifications-sentinel">
            {notificationsQuery.isFetchingNextPage && <span>{t('app.loading')}</span>}
          </div>
        </div>
      )}
    </div>
  );
}
