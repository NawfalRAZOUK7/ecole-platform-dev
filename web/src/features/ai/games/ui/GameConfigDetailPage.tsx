import { useTranslation } from 'react-i18next';
import { useNavigate, useParams } from 'react-router-dom';
import { Badge, EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { GameConfigEditor } from './GameConfigEditor';
import { useGameConfig } from '../model/useGames';

function getAgeRangeLabel(min: number | null, max: number | null, fallback: string) {
  if (min === null && max === null) {
    return fallback;
  }

  if (min !== null && max !== null) {
    return `${min}-${max}`;
  }

  return String(min ?? max ?? fallback);
}

export function GameConfigDetailPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const configQuery = useGameConfig(id);

  if (configQuery.isLoading) {
    return <LoadingState />;
  }

  if (!configQuery.data) {
    return (
      <div className="page">
        <div className="page-header page-header--split">
          <div>
            <h1 className="page-title">{t('games.detailTitle')}</h1>
            <p className="page-subtitle">{t('games.detailSubtitle')}</p>
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/teacher/games')}
          >
            {t('games.backToList')}
          </button>
        </div>

        <ErrorBanner
          error={configQuery.error instanceof Error ? configQuery.error.message : null}
          onRetry={() => void configQuery.refetch()}
        />
        <EmptyState message={t('games.notFound')} icon="🔎" />
      </div>
    );
  }

  const config = configQuery.data;

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{config.title}</h1>
          <p className="page-subtitle">{t('games.detailSubtitle')}</p>
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/teacher/games')}
          >
            {t('games.backToList')}
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => navigate('/teacher/games/new')}
          >
            {t('games.createGame')}
          </button>
        </div>
      </div>

      <ErrorBanner
        error={configQuery.error instanceof Error ? configQuery.error.message : null}
        onRetry={() => void configQuery.refetch()}
      />

      <section className="card" style={{ padding: 20, marginBottom: 20 }}>
        <div
          style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}
        >
          <div>
            <h2 style={{ marginTop: 0, marginBottom: 8 }}>{t('games.detailTitle')}</h2>
            <p style={{ margin: 0, color: 'var(--color-text-secondary)' }}>
              {t(`games.types.${config.gameType}`)} • {t(`games.difficulties.${config.difficulty}`)}
            </p>
          </div>
          <Badge variant={config.isActive ? 'success' : 'neutral'}>
            {t(config.isActive ? 'games.status.active' : 'games.status.inactive')}
          </Badge>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: 16,
            marginTop: 20,
          }}
        >
          <div>
            <strong>{t('games.table.subject')}</strong>
            <div>{config.subject || '—'}</div>
          </div>
          <div>
            <strong>{t('games.cards.ageTitle')}</strong>
            <div>
              {getAgeRangeLabel(
                config.targetAgeMin,
                config.targetAgeMax,
                t('games.cards.noAgeRange'),
              )}
            </div>
          </div>
          <div>
            <strong>{t('games.table.reward')}</strong>
            <div>{t('games.cards.reward', { stars: config.rewardStars, xp: config.rewardXp })}</div>
          </div>
          <div>
            <strong>{t('games.table.updated')}</strong>
            <div>{new Date(config.updatedAt).toLocaleString()}</div>
          </div>
          <div>
            <strong>{t('games.form.titleAr')}</strong>
            <div>{config.titleAr || '—'}</div>
          </div>
          <div>
            <strong>{t('games.form.titleFr')}</strong>
            <div>{config.titleFr || '—'}</div>
          </div>
        </div>

        <div style={{ marginTop: 20 }}>
          <strong>{t('games.previewTitle')}</strong>
          <pre
            style={{
              marginTop: 8,
              padding: 16,
              borderRadius: 8,
              background: 'var(--color-surface-secondary, #f5f5f5)',
              overflowX: 'auto',
              fontSize: 13,
            }}
          >
            {JSON.stringify(config.config, null, 2)}
          </pre>
        </div>
      </section>

      <GameConfigEditor
        config={config}
        embedded
        onSaved={() => void configQuery.refetch()}
        onCancel={() => navigate('/teacher/games')}
      />
    </div>
  );
}
