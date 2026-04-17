import { useTranslation } from 'react-i18next';
import { formatDate } from '@/shared/i18n';

interface StreakCardProps {
  currentStreak: number;
  longestStreak: number;
  lastActivityAt: string | null;
}

export function StreakCard({ currentStreak, longestStreak, lastActivityAt }: StreakCardProps) {
  const { t, i18n } = useTranslation();

  return (
    <section className="card" style={{ padding: 20, display: 'grid', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontSize: 28, color: 'var(--kids-streak-orange)' }} aria-hidden="true">
          🔥
        </span>
        <div>
          <strong style={{ fontSize: 22 }}>{t('rewards.streak.title')}</strong>
          <div style={{ color: 'var(--color-text-secondary)' }}>{t('rewards.streak.subtitle')}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
        <div>
          <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
            {t('rewards.streak.current')}
          </div>
          <strong style={{ fontSize: 24 }}>{currentStreak}</strong>
        </div>
        <div>
          <div style={{ color: 'var(--color-text-secondary)', fontSize: 13 }}>
            {t('rewards.streak.longest')}
          </div>
          <strong style={{ fontSize: 24 }}>{longestStreak}</strong>
        </div>
      </div>

      <div style={{ color: 'var(--color-text-secondary)' }}>
        {t('rewards.stats.lastActivity')}:{' '}
        <strong>
          {lastActivityAt ? formatDate(lastActivityAt, i18n.language) : t('rewards.history.none')}
        </strong>
      </div>
    </section>
  );
}
