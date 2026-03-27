import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, ApiClientError } from '@/services/api/client';
import { ErrorBanner } from '@/shared/ui/ErrorBanner';
import { LoadingState } from '@/shared/ui/LoadingState';
import { EmptyState } from '@/shared/ui/EmptyState';
import { formatDate } from '@/shared/i18n';
import type { NotificationItem } from './types';

const CATEGORY_OPTIONS = ['academic', 'billing', 'attendance', 'system', 'announcement'] as const;
const CHANNEL_OPTIONS = ['in_app', 'push', 'email', 'sms'] as const;

export function NotificationsPage() {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [category, setCategory] = useState('');
  const [channel, setChannel] = useState('');
  const [readFilter, setReadFilter] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  const filters = useMemo(
    () => ({ category, channel, readFilter, fromDate, toDate }),
    [category, channel, readFilter, fromDate, toDate]
  );

  const fetchNotifications = useCallback(async (cursor?: string, append = false) => {
    const params: Record<string, string | number | undefined> = {
      limit: 20,
      cursor,
      category: category || undefined,
      channel: channel || undefined,
      read: readFilter === '' ? undefined : readFilter,
      from: fromDate || undefined,
      to: toDate || undefined,
    };

    try {
      const resp = await api.list<NotificationItem>('/notifications', params);
      setItems((prev) => (append ? [...prev, ...resp.data] : resp.data));
      setNextCursor(resp.meta.next_cursor);
      setHasMore(resp.meta.has_more);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : t('app.error'));
    }
  }, [category, channel, fromDate, readFilter, t, toDate]);

  useEffect(() => {
    setLoading(true);
    void fetchNotifications().finally(() => setLoading(false));
  }, [fetchNotifications, filters]);

  useEffect(() => {
    if (!hasMore || loading || loadingMore || !sentinelRef.current) return;

    const observer = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting && nextCursor) {
        setLoadingMore(true);
        void fetchNotifications(nextCursor, true).finally(() => setLoadingMore(false));
      }
    }, { threshold: 0.2 });

    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [fetchNotifications, hasMore, loading, loadingMore, nextCursor]);

  async function handleMarkRead(notification: NotificationItem, read = true) {
    await api.patch(`/notifications/${notification.id}/read`, { read });
    setItems((prev) => prev.map((item) => (
      item.id === notification.id
        ? {
            ...item,
            is_read: read,
            read_at: read ? new Date().toISOString() : null,
          }
        : item
    )));
  }

  async function handleMarkAllRead() {
    await api.patch('/notifications/mark-all-read');
    setItems((prev) => prev.map((item) => ({
      ...item,
      is_read: true,
      read_at: item.read_at || new Date().toISOString(),
    })));
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

  if (loading) {
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

      <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={() => void fetchNotifications()} />

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
            {loadingMore && <span>{t('app.loading')}</span>}
          </div>
        </div>
      )}
    </div>
  );
}
