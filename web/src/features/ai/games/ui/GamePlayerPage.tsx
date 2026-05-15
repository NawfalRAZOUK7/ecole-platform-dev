import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ErrorBanner, LoadingState } from '@/shared/ui';
import { useGameConfig } from '../model/useGames';
import { MemoryMatchGame } from './MemoryMatchGame';
import { SortingGame } from './SortingGame';
import { VocabularyCardsGame } from './VocabularyCardsGame';

export function GamePlayerPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const configQuery = useGameConfig(id);

  if (configQuery.isLoading || !configQuery.data) {
    return <LoadingState />;
  }

  if (configQuery.error) {
    return (
      <div className="page">
        <ErrorBanner
          error={configQuery.error instanceof Error ? configQuery.error.message : 'Error'}
          onRetry={() => void configQuery.refetch()}
        />
      </div>
    );
  }

  const game = configQuery.data;
  const onExit = () => navigate('/student/games');

  return (
    <div className="page">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button type="button" className="btn btn-secondary" onClick={onExit}>
          ← {t('app.back', 'Retour')}
        </button>
        <h1 className="page-title" style={{ margin: 0 }}>
          {game.titleFr || game.title}
        </h1>
      </div>

      {game.gameType === 'memory_match' ? (
        <MemoryMatchGame game={game} onExit={onExit} />
      ) : game.gameType === 'sorting' ? (
        <SortingGame game={game} onExit={onExit} />
      ) : (
        <VocabularyCardsGame game={game} onExit={onExit} />
      )}
    </div>
  );
}
