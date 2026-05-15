import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { BadgeShelf } from './BadgeShelf';
import { LevelBadge } from './LevelBadge';
import { RewardHistoryList } from './RewardHistoryList';
import { StarCounter } from './StarCounter';
import { StreakCard } from './StreakCard';
import type { Badge, RewardEvent, StudentRewards } from '../api/rewards.api';

interface RewardsOverviewProps {
  rewards: StudentRewards;
  badges: Badge[];
  history: RewardEvent[];
  leaderboardHref?: string | null;
}

export function RewardsOverview({
  rewards,
  badges,
  history,
  leaderboardHref = null,
}: RewardsOverviewProps) {
  const { t } = useTranslation();

  return (
    <div style={{ display: 'grid', gap: 20 }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
          gap: 16,
        }}
      >
        <LevelBadge level={rewards.level} xp={rewards.xp} progress={rewards.levelProgress} />
        <StarCounter value={rewards.stars} />
        <StreakCard
          currentStreak={rewards.streakDays}
          longestStreak={rewards.longestStreak}
          lastActivityAt={rewards.lastActivityAt}
        />
      </div>

      {leaderboardHref ? (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Link className="btn btn-secondary" to={leaderboardHref}>
            {t('rewards.viewLeaderboard')}
          </Link>
        </div>
      ) : null}

      <BadgeShelf earnedCodes={rewards.badges} badges={badges} />
      <RewardHistoryList events={history} />
    </div>
  );
}
