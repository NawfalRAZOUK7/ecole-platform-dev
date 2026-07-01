import { useTranslation } from 'react-i18next';
import { xpThresholdForLevel } from '../api/rewards.api';
import { space } from '@/shared/ui/tokens';

interface LevelBadgeProps {
  level: number;
  xp: number;
  progress: number;
}

export function LevelBadge({ level, xp, progress }: LevelBadgeProps) {
  const { t } = useTranslation();
  const clampedProgress = Math.max(0, Math.min(100, progress));
  const xpToNextLevel = Math.max(0, xpThresholdForLevel(level + 1) - xp);

  return (
    <section className="card" style={{ padding: 20, display: 'grid', gap: space.base }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: space.base }}>
        <div
          style={{
            width: 72,
            height: 72,
            borderRadius: '50%',
            display: 'grid',
            placeItems: 'center',
            background:
              'linear-gradient(135deg, var(--kids-star-gold) 0%, var(--kids-streak-orange) 100%)',
            color: '#2f1b0c',
            fontWeight: 800,
            fontSize: 22,
          }}
        >
          {level}
        </div>
        <div>
          <div
            style={{
              fontSize: 12,
              textTransform: 'uppercase',
              color: 'var(--color-text-secondary)',
            }}
          >
            {t('rewards.progress.title')}
          </div>
          <strong style={{ fontSize: 22 }}>
            {t('rewards.stats.level')} {level}
          </strong>
          <div style={{ color: 'var(--color-text-secondary)', marginTop: 4 }}>
            {t('rewards.level.xpSummary', { xp })}
          </div>
        </div>
      </div>

      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, gap: 12 }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>
            {t('rewards.level.progress')}
          </span>
          <strong>{Math.round(clampedProgress)}%</strong>
        </div>
        <div
          style={{
            width: '100%',
            height: 12,
            borderRadius: 999,
            overflow: 'hidden',
            background: 'var(--color-bg-muted)',
          }}
        >
          <div
            style={{
              width: `${clampedProgress}%`,
              height: '100%',
              borderRadius: 999,
              background:
                'linear-gradient(90deg, var(--kids-star-gold) 0%, var(--kids-streak-orange) 100%)',
            }}
          />
        </div>
      </div>

      <div style={{ color: 'var(--color-text-secondary)' }}>
        {t('rewards.stats.nextLevel')}: <strong>{xpToNextLevel}</strong>
      </div>
    </section>
  );
}
