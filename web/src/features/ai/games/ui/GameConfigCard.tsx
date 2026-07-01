import { useTranslation } from 'react-i18next';
import { Badge } from '@/shared/ui/Badge';
import { space } from '@/shared/ui/tokens';
import type { GameConfig } from '../model/types';

interface GameConfigCardProps {
  config: GameConfig;
  onClick: () => void;
}

const GAME_TYPE_COLOR: Record<string, string> = {
  memory: 'var(--kids-game-blue)',
  sorting: 'var(--kids-game-green)',
  vocabulary: 'var(--kids-game-purple)',
};

function getGameTypeColor(gameType: string): string {
  return GAME_TYPE_COLOR[gameType] ?? 'var(--kids-game-card-back)';
}

function getAgeRangeLabel(config: GameConfig, fallback: string) {
  if (config.targetAgeMin === null && config.targetAgeMax === null) {
    return fallback;
  }

  if (config.targetAgeMin !== null && config.targetAgeMax !== null) {
    return `${config.targetAgeMin}-${config.targetAgeMax}`;
  }

  return String(config.targetAgeMin ?? config.targetAgeMax ?? fallback);
}

export function GameConfigCard({ config, onClick }: GameConfigCardProps) {
  const { t } = useTranslation();

  return (
    <button
      type="button"
      className="card"
      onClick={onClick}
      style={{
        width: '100%',
        textAlign: 'left',
        padding: space.base,
        cursor: 'pointer',
        display: 'grid',
        gap: space.md,
        borderLeft: `4px solid ${getGameTypeColor(config.gameType)}`,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: space.md,
          alignItems: 'start',
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: 16 }}>{config.title}</h3>
          <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: 13 }}>
            {t(`games.types.${config.gameType}`, { defaultValue: config.gameType })}
          </p>
        </div>
        <Badge variant={config.isActive ? 'success' : 'neutral'}>
          {t(config.isActive ? 'games.status.active' : 'games.status.inactive')}
        </Badge>
      </div>

      <div style={{ display: 'flex', gap: space.sm, flexWrap: 'wrap' }}>
        <Badge variant="info">
          {t(`games.difficulties.${config.difficulty}`, { defaultValue: config.difficulty })}
        </Badge>
        <Badge variant="warning">
          {t('games.cards.ageRange', {
            value: getAgeRangeLabel(config, t('games.cards.noAgeRange')),
          })}
        </Badge>
        <Badge variant="success">
          {t('games.cards.reward', {
            stars: config.rewardStars,
            xp: config.rewardXp,
          })}
        </Badge>
      </div>

      <div style={{ color: 'var(--color-text-secondary)', fontSize: 13, display: 'grid', gap: 4 }}>
        <span>
          {t('games.table.subject')}: {config.subject || '—'}
        </span>
        <span>
          {t('games.table.updated')}: {new Date(config.updatedAt).toLocaleDateString()}
        </span>
      </div>
    </button>
  );
}
