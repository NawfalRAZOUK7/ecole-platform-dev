import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useDismissibleError } from '@/shared/hooks/useDismissibleError';
import { EmptyState, ErrorBanner, LoadingState, SearchInput, Tabs } from '@/shared/ui';
import { Badge } from '@/shared/ui/Badge';
import { toBannerError } from '@/shared/ui/errorUtils';
import type { Activity } from '../api/activities.api';
import { useActivities } from '../model/useActivities';

type ActivityTypeTab = {
  id: string;
  label: string;
};

const ACTIVITY_TYPE_LABELS: Record<string, string> = {
  all: 'activities.typeAll',
  assessment: 'activities.types.assessment',
  exercise: 'activities.types.exercise',
  game: 'activities.types.game',
  general: 'activities.types.general',
  practice: 'activities.types.practice',
  project: 'activities.types.project',
  quiz: 'activities.types.quiz',
  reading: 'activities.types.reading',
  simulation: 'activities.types.simulation',
  video: 'activities.types.video',
  worksheet: 'activities.types.worksheet',
};

function getActivityType(activity: Activity) {
  return activity.activity_type || activity.type || 'general';
}

export function ActivitiesPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [search, setSearch] = useState('');
  const [difficulty, setDifficulty] = useState('all');
  const activitiesQuery = useActivities({
    difficulty: difficulty === 'all' ? undefined : difficulty,
    search: search || undefined,
  });
  const items = useMemo(
    () => activitiesQuery.data?.pages.flatMap((page) => page.data) ?? [],
    [activitiesQuery.data],
  );
  const errorState = useDismissibleError(toBannerError(activitiesQuery.error, t('app.error')));

  const activityTypes = useMemo<ActivityTypeTab[]>(() => {
    const discoveredTypes = Array.from(new Set(items.map((activity) => getActivityType(activity))));
    return [
      { id: 'all', label: ACTIVITY_TYPE_LABELS.all },
      ...discoveredTypes.map((type) => ({
        id: type,
        label: ACTIVITY_TYPE_LABELS[type] || type,
      })),
    ];
  }, [items]);

  const hasActivities = items.length > 0;

  if (activitiesQuery.isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('activities.title')}</h1>
          <p className="page-subtitle">{t('activities.subtitle')}</p>
        </div>
        <div className="page-actions">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="activities.searchPlaceholder"
          />
          <select
            className="filter-select"
            value={difficulty}
            aria-label={t('activities.difficulty')}
            onChange={(event) => setDifficulty(event.target.value)}
          >
            <option value="all">{t('activities.allDifficulties')}</option>
            <option value="easy">{t('activities.difficultyEasy')}</option>
            <option value="medium">{t('activities.difficultyMedium')}</option>
            <option value="hard">{t('activities.difficultyHard')}</option>
          </select>
        </div>
      </div>

      <ErrorBanner
        error={errorState.error}
        onDismiss={errorState.dismiss}
        onRetry={() => void activitiesQuery.refetch()}
      />

      {!hasActivities ? (
        <EmptyState message={t('activities.empty')} icon="🎯" />
      ) : (
        <>
          <Tabs
            defaultTab="all"
            tabs={activityTypes.map((tab) => {
              const filteredItems =
                tab.id === 'all'
                  ? items
                  : items.filter((activity) => getActivityType(activity) === tab.id);

              return {
                id: tab.id,
                label: tab.label,
                content:
                  filteredItems.length === 0 ? (
                    <EmptyState message={t('activities.emptyFiltered')} icon="🔎" />
                  ) : (
                    <div className="card-list">
                      {filteredItems.map((activity) => {
                        const type = getActivityType(activity);
                        const objective = activity.objective || activity.pedagogical_objective;

                        return (
                          <article key={activity.id} className="card activity-card">
                            <div className="activity-header">
                              <Badge variant="info">{t(`activities.types.${type}`)}</Badge>
                              {activity.difficulty ? (
                                <Badge variant="neutral">
                                  {t(`activities.difficultyValue.${activity.difficulty}`, {
                                    defaultValue: activity.difficulty,
                                  })}
                                </Badge>
                              ) : null}
                            </div>
                            <h3 className="activity-title">{activity.title}</h3>
                            {objective ? <p className="activity-objective">{objective}</p> : null}
                            <div className="page-actions">
                              <button
                                type="button"
                                className="btn btn-secondary"
                                onClick={() => navigate(`/activities/${activity.id}`)}
                              >
                                {t('activities.viewDetails')}
                              </button>
                            </div>
                          </article>
                        );
                      })}
                    </div>
                  ),
              };
            })}
          />

          {activitiesQuery.hasNextPage ? (
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <button
                className="btn btn-secondary"
                onClick={() => void activitiesQuery.fetchNextPage()}
                disabled={activitiesQuery.isFetchingNextPage}
              >
                {activitiesQuery.isFetchingNextPage ? t('app.loading') : t('feed.loadMore')}
              </button>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
