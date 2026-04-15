export {
  rewardsService,
  type AwardRewardPayload,
  type AwardRewardResult,
  type Badge,
  type LeaderboardEntry,
  type RewardEvent,
  type StudentRewards,
} from '@/services/rewards.service';

export function xpThresholdForLevel(level: number): number {
  if (level <= 1) {
    return 0;
  }

  return 50 * (level - 1) * level;
}
