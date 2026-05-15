import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { GAME_TYPES, type GameConfig, type GameType } from '../model/types';
import { useGameConfigs } from '../model/useGames';

const GAME_ICONS: Record<GameType, string> = {
  memory_match: '🧠',
  sorting: '🗂️',
  vocabulary_cards: '📖',
};

const DIFFICULTY_BADGE: Record<string, { label: string; color: string }> = {
  easy: { label: 'Facile', color: '#10b981' },
  medium: { label: 'Moyen', color: '#f59e0b' },
  hard: { label: 'Difficile', color: '#ef4444' },
};

export function StudentGamesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [selectedType, setSelectedType] = useState<GameType | ''>('');

  const configsQuery = useGameConfigs({
    gameType: selectedType || undefined,
    isActive: true,
  });

  const items = useMemo(
    () => configsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [configsQuery.data],
  );

  if (configsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title" style={{ fontSize: 32 }}>
          {GAME_ICONS.memory_match} {t('studentGames.title', 'Mes jeux')}
        </h1>
        <p className="page-subtitle">
          {t('studentGames.subtitle', 'Choisis un jeu pour apprendre en t’amusant !')}
        </p>
      </div>

      <ErrorBanner
        error={configsQuery.error instanceof Error ? configsQuery.error.message : null}
        onRetry={() => void configsQuery.refetch()}
      />

      <div
        style={{
          display: 'flex',
          gap: 8,
          flexWrap: 'wrap',
          marginBottom: 20,
        }}
      >
        <FilterChip
          active={selectedType === ''}
          label={t('studentGames.all', 'Tous')}
          onClick={() => setSelectedType('')}
        />
        {GAME_TYPES.map((gameType) => (
          <FilterChip
            key={gameType}
            active={selectedType === gameType}
            label={`${GAME_ICONS[gameType]} ${t(`games.types.${gameType}`)}`}
            onClick={() => setSelectedType(gameType)}
          />
        ))}
      </div>

      {items.length === 0 ? (
        <EmptyState
          message={t('studentGames.empty', 'Aucun jeu disponible. Reviens plus tard !')}
          icon="🎮"
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
            gap: 16,
          }}
        >
          {items.map((game) => (
            <StudentGameCard
              key={game.id}
              game={game}
              onPlay={() => navigate(`/student/games/${game.id}/play`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface FilterChipProps {
  active: boolean;
  label: string;
  onClick: () => void;
}

function FilterChip({ active, label, onClick }: FilterChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        padding: '8px 16px',
        borderRadius: 999,
        border: active ? '2px solid var(--color-primary)' : '2px solid var(--color-border)',
        background: active ? 'var(--color-primary)' : 'var(--color-surface)',
        color: active ? '#fff' : 'var(--color-text)',
        cursor: 'pointer',
        fontSize: 14,
        fontWeight: 600,
      }}
    >
      {label}
    </button>
  );
}

interface StudentGameCardProps {
  game: GameConfig;
  onPlay: () => void;
}

function StudentGameCard({ game, onPlay }: StudentGameCardProps) {
  const difficulty = DIFFICULTY_BADGE[game.difficulty] ?? DIFFICULTY_BADGE.easy;
  const icon = GAME_ICONS[game.gameType];

  return (
    <button
      type="button"
      onClick={onPlay}
      className="card"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        padding: 20,
        border: '2px solid var(--color-border)',
        background: 'var(--color-surface)',
        borderRadius: 'var(--radius-lg, 16px)',
        cursor: 'pointer',
        textAlign: 'left',
        transition: 'transform 0.15s ease, box-shadow 0.15s ease',
        boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 8px 16px rgba(0,0,0,0.12)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
      }}
    >
      <div style={{ fontSize: 48 }}>{icon}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text)' }}>
        {game.titleFr || game.title}
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <span
          style={{
            padding: '2px 8px',
            borderRadius: 999,
            background: difficulty.color,
            color: '#fff',
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          {difficulty.label}
        </span>
        {game.subject ? (
          <span
            style={{
              padding: '2px 8px',
              borderRadius: 999,
              background: 'var(--color-bg-secondary)',
              color: 'var(--color-text)',
              fontSize: 12,
            }}
          >
            {game.subject}
          </span>
        ) : null}
      </div>
      <div style={{ display: 'flex', gap: 12, color: 'var(--color-text-secondary)', fontSize: 14 }}>
        <span>⭐ {game.rewardStars}</span>
        <span>✨ {game.rewardXp} XP</span>
      </div>
    </button>
  );
}
