import { api } from '@/services/api/client';

export interface StudentRewards {
  id: string;
  student_id: string;
  stars: number;
  xp: number;
  level: number;
  streak_days: number;
  badges: string[];
  last_activity_at: string | null;
  level_progress: number;
}

export interface RewardHistoryEntry {
  id: string;
  event_type: string;
  stars_earned: number;
  xp_earned: number;
  source_type: string | null;
  source_id: string | null;
  created_at: string;
}

export interface RewardLeaderboardEntry {
  student_id: string;
  student_name: string;
  stars: number;
  level: number;
  rank: number;
}

export interface RewardBadge {
  code: string;
  title: string | null;
  icon: string | null;
}

export interface AwardRewardPayload {
  student_id: string;
  event_type: string;
  stars: number;
  xp: number;
  source_type?: string | null;
  source_id?: string | null;
}

export interface CreateRewardBadgePayload {
  code: string;
  title?: string | null;
  icon?: string | null;
}

export interface AwardRewardResponse extends StudentRewards {
  newly_earned_badges: RewardBadge[];
}

export function xpThresholdForLevel(level: number): number {
  if (level <= 1) {
    return 0;
  }

  return 50 * (level - 1) * level;
}

export const rewardsService = {
  getMyRewards() {
    return api.get<StudentRewards>('/rewards/me');
  },

  getStudentRewards(studentId: string) {
    return api.get<StudentRewards>(`/rewards/student/${studentId}`);
  },

  getStudentHistory(studentId: string) {
    return api.get<RewardHistoryEntry[]>(`/rewards/student/${studentId}/history`);
  },

  getLeaderboard(classId: string, limit: number) {
    return api.list<RewardLeaderboardEntry>(`/rewards/leaderboard/${classId}`, { limit });
  },

  listBadges() {
    return api.get<RewardBadge[]>('/rewards/badges');
  },

  createBadge(payload: CreateRewardBadgePayload) {
    return api.post<RewardBadge>('/rewards/badges', payload);
  },

  awardReward(payload: AwardRewardPayload) {
    return api.post<AwardRewardResponse>('/rewards/award', payload);
  },
};
