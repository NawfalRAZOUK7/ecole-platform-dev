import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/services/auth/AuthContext';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { GameConfigCard } from './GameConfigCard';
import { GAME_DIFFICULTIES, GAME_TYPES, type Difficulty, type GameType } from './types';
import { useGameConfigs } from './useGames';

type StatusFilter = 'all' | 'active' | 'inactive';

function parseTargetAge(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }

  const parsed = Number(value);
  return Number.isNaN(parsed) ? undefined : parsed;
}

export function GamesListPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [gameTypeFilter, setGameTypeFilter] = useState<GameType | ''>('');
  const [difficultyFilter, setDifficultyFilter] = useState<Difficulty | ''>('');
  const [subjectFilter, setSubjectFilter] = useState('');
  const [targetAgeFilter, setTargetAgeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');

  const filters = useMemo(
    () => ({
      gameType: gameTypeFilter || undefined,
      difficulty: difficultyFilter || undefined,
      subject: subjectFilter.trim() || undefined,
      targetAge: parseTargetAge(targetAgeFilter),
      isActive: statusFilter === 'active' ? true : statusFilter === 'inactive' ? false : undefined,
    }),
    [difficultyFilter, gameTypeFilter, statusFilter, subjectFilter, targetAgeFilter],
  );

  const configsQuery = useGameConfigs(filters);
  const items = useMemo(
    () => configsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [configsQuery.data],
  );
  const canManageGames = user?.role === 'TCH' || user?.role === 'ADM';

  if (configsQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('games.title')}</h1>
          <p className="page-subtitle">{t('games.subtitle')}</p>
        </div>
        {canManageGames ? (
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => navigate('/teacher/games/new')}
          >
            {t('games.createGame')}
          </button>
        ) : null}
      </div>

      <ErrorBanner
        error={configsQuery.error instanceof Error ? configsQuery.error.message : null}
        onRetry={() => void configsQuery.refetch()}
      />

      <div className="filters-bar">
        <select
          className="filter-select"
          value={gameTypeFilter}
          onChange={(event) => setGameTypeFilter(event.target.value as GameType | '')}
        >
          <option value="">{t('games.filters.allTypes')}</option>
          {GAME_TYPES.map((gameType) => (
            <option key={gameType} value={gameType}>
              {t(`games.types.${gameType}`)}
            </option>
          ))}
        </select>

        <select
          className="filter-select"
          value={difficultyFilter}
          onChange={(event) => setDifficultyFilter(event.target.value as Difficulty | '')}
        >
          <option value="">{t('games.filters.allDifficulties')}</option>
          {GAME_DIFFICULTIES.map((difficulty) => (
            <option key={difficulty} value={difficulty}>
              {t(`games.difficulties.${difficulty}`)}
            </option>
          ))}
        </select>

        <input
          type="text"
          className="filter-input"
          placeholder={t('games.filters.subjectPlaceholder')}
          value={subjectFilter}
          onChange={(event) => setSubjectFilter(event.target.value)}
        />

        <input
          type="number"
          min="0"
          max="18"
          className="filter-input"
          placeholder={t('games.filters.targetAgePlaceholder')}
          value={targetAgeFilter}
          onChange={(event) => setTargetAgeFilter(event.target.value)}
        />

        <select
          className="filter-select"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
        >
          <option value="all">{t('games.filters.allStatuses')}</option>
          <option value="active">{t('games.status.active')}</option>
          <option value="inactive">{t('games.status.inactive')}</option>
        </select>
      </div>

      {items.length === 0 ? (
        <EmptyState message={t('games.emptyKids')} icon="🎮" />
      ) : (
        <>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: 16,
            }}
          >
            {items.map((config) => (
              <GameConfigCard
                key={config.id}
                config={config}
                onClick={() => navigate(`/teacher/games/${config.id}`)}
              />
            ))}
          </div>

          {configsQuery.hasNextPage ? (
            <div style={{ marginTop: 20, textAlign: 'center' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => void configsQuery.fetchNextPage()}
                disabled={configsQuery.isFetchingNextPage}
              >
                {configsQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
