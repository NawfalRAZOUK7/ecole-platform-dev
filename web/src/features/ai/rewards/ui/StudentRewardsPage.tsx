import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { EmptyState, ErrorBanner, LoadingState } from '@/shared/ui';
import { RewardsOverview } from './RewardsOverview';
import { useRewardBadges, useStudentRewardHistory, useStudentRewards } from '../model/useRewards';

export function StudentRewardsPage() {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const rewardsQuery = useStudentRewards(id, Boolean(id));
  const badgesQuery = useRewardBadges(Boolean(id));
  const historyQuery = useStudentRewardHistory(id, 10, Boolean(id));

  if (rewardsQuery.isLoading || badgesQuery.isLoading || historyQuery.isLoading) {
    return <LoadingState />;
  }

  if (!id || !rewardsQuery.data) {
    return (
      <div className="page">
        <div className="page-header page-header--split">
          <div>
            <h1 className="page-title">{t('rewards.studentTitle')}</h1>
            <p className="page-subtitle">{t('rewards.studentSubtitle')}</p>
          </div>
        </div>
        <ErrorBanner
          error={
            rewardsQuery.error instanceof Error
              ? rewardsQuery.error.message
              : badgesQuery.error instanceof Error
                ? badgesQuery.error.message
                : historyQuery.error instanceof Error
                  ? historyQuery.error.message
                  : null
          }
          onRetry={() => {
            void Promise.all([
              rewardsQuery.refetch(),
              badgesQuery.refetch(),
              historyQuery.refetch(),
            ]);
          }}
        />
        <EmptyState message={t('rewards.noRewardsYet')} icon="⭐" />
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header page-header--split">
        <div>
          <h1 className="page-title">{t('rewards.studentTitle')}</h1>
          <p className="page-subtitle">{t('rewards.studentSubtitle')}</p>
        </div>
      </div>

      <ErrorBanner
        error={
          rewardsQuery.error instanceof Error
            ? rewardsQuery.error.message
            : badgesQuery.error instanceof Error
              ? badgesQuery.error.message
              : historyQuery.error instanceof Error
                ? historyQuery.error.message
                : null
        }
        onRetry={() => {
          void Promise.all([rewardsQuery.refetch(), badgesQuery.refetch(), historyQuery.refetch()]);
        }}
      />

      <RewardsOverview
        rewards={rewardsQuery.data}
        badges={badgesQuery.data ?? []}
        history={historyQuery.data ?? []}
      />
    </div>
  );
}
