import { useTranslation } from 'react-i18next';
import { EmptyState } from '@/shared/ui';
import { formatDate } from '@/shared/i18n';
import type { RewardEvent } from './rewards.service';

interface RewardHistoryListProps {
  events: RewardEvent[];
}

export function RewardHistoryList({ events }: RewardHistoryListProps) {
  const { t, i18n } = useTranslation();

  if (events.length === 0) {
    return <EmptyState message={t('rewards.history.empty')} icon="✨" />;
  }

  return (
    <section className="card" style={{ padding: 20 }}>
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>{t('rewards.history.title')}</h2>
        <p style={{ margin: '6px 0 0', color: 'var(--color-text-secondary)' }}>
          {t('rewards.history.subtitle')}
        </p>
      </div>

      <div style={{ display: 'grid', gap: 12 }}>
        {events.slice(0, 10).map((event) => (
          <article
            key={event.id}
            style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1fr) auto',
              gap: 12,
              padding: '12px 0',
              borderBottom: '1px solid var(--color-border)',
            }}
          >
            <div style={{ display: 'grid', gap: 4 }}>
              <strong>
                {t(`rewards.events.${event.eventType}`, { defaultValue: event.eventType })}
              </strong>
              <span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
                {event.sourceType
                  ? t(`rewards.sources.${event.sourceType}`, { defaultValue: event.sourceType })
                  : t('rewards.history.none')}
              </span>
              <span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
                {formatDate(event.createdAt, i18n.language)}
              </span>
            </div>
            <div style={{ textAlign: 'right', display: 'grid', gap: 4, alignContent: 'start' }}>
              <strong>+{event.starsEarned} ⭐</strong>
              <span style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
                +{event.xpEarned} XP
              </span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
