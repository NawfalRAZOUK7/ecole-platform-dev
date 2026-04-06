import { useTranslation } from 'react-i18next';
import { formatDate } from '@/shared/i18n';
import { Badge } from '@/shared/ui';
import type { FeedItem as FeedRecord } from './types';

interface FeedItemCardProps {
  item: FeedRecord;
  isRead: boolean;
  onOpen: (item: FeedRecord) => void;
  onMarkAsRead: (itemId: string) => void;
}

const TYPE_ICONS: Record<string, string> = {
  announcement: '📢',
  attendance: '✅',
  attendance_alert: '⚠️',
  feed_new: '📰',
  grade: '📊',
  grade_published: '📊',
  invoice: '🧾',
  message: '💬',
  payment: '💳',
};

function getBadgeVariant(itemType: string) {
  if (['attendance_alert'].includes(itemType)) {
    return 'warning' as const;
  }
  if (['grade', 'grade_published', 'payment'].includes(itemType)) {
    return 'success' as const;
  }

  return 'info' as const;
}

export function FeedItemCard({
  item,
  isRead,
  onOpen,
  onMarkAsRead,
}: FeedItemCardProps) {
  const { t, i18n } = useTranslation();
  const itemType = item.item_type || 'feed_new';
  const icon = TYPE_ICONS[itemType] || '📰';

  return (
    <article
      className="card feed-item"
      style={{
        opacity: isRead ? 0.78 : 1,
        borderLeft: isRead ? '4px solid var(--color-border)' : '4px solid var(--color-primary)',
      }}
    >
      <div className="feed-item-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 20 }} aria-hidden="true">{icon}</span>
          <Badge variant={getBadgeVariant(itemType)}>
            {t(`feed.types.${itemType}`, { defaultValue: itemType })}
          </Badge>
          {!isRead ? (
            <Badge variant="warning">{t('feed.unread')}</Badge>
          ) : null}
        </div>
        <time className="feed-date">
          {formatDate(item.published_at, i18n.language, {
            dateStyle: 'medium',
            timeStyle: 'short',
          })}
        </time>
      </div>

      <h3 className="feed-title">{item.title}</h3>
      {item.summary ? <p className="feed-summary">{item.summary}</p> : null}

      <div className="page-actions">
        <button type="button" className="btn btn-primary" onClick={() => onOpen(item)}>
          {t('feed.open')}
        </button>
        {!isRead ? (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => onMarkAsRead(item.id)}
          >
            {t('feed.markRead')}
          </button>
        ) : null}
      </div>
    </article>
  );
}
