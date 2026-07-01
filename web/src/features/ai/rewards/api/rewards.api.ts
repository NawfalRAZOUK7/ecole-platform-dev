import { api } from '@/core/api/client';

export interface StudentRewards {
  id: string;
  studentId: string;
  stars: number;
  xp: number;
  level: number;
  streakDays: number;
  longestStreak: number;
  badges: string[];
  lastActivityAt: string | null;
  levelProgress: number;
}

export interface RewardEvent {
  id: string;
  eventType: string;
  starsEarned: number;
  xpEarned: number;
  sourceType: string | null;
  sourceId: string | null;
  createdAt: string;
}

export interface LeaderboardEntry {
  studentId: string;
  studentName: string;
  stars: number;
  level: number;
  rank: number;
}

export interface Badge {
  id: string;
  code: string;
  titleFr: string;
  titleAr: string;
  titleEn: string;
  descriptionFr: string | null;
  descriptionAr: string | null;
  descriptionEn: string | null;
  icon: string | null;
  criteriaType: string;
  criteriaValue: number;
  displayOrder: number;
  isActive: boolean;
}

export interface AwardRewardPayload {
  student_id: string;
  event_type: string;
  stars: number;
  xp: number;
  source_type?: string;
  source_id?: string;
}

export interface AwardRewardResult {
  reward: StudentRewards;
  newly_earned_badges: string[];
}

interface RawStudentRewards {
  id?: string;
  student_id?: string;
  studentId?: string;
  stars?: number;
  xp?: number;
  total_xp?: number;
  level: number;
  next_level_xp?: number;
  streak_days?: number;
  streakDays?: number;
  longest_streak?: number;
  longestStreak?: number;
  badges?: string[];
  badge_ids?: string[];
  recent_events?: RawRewardEvent[];
  last_activity_at?: string | null;
  lastActivityAt?: string | null;
  level_progress?: number;
  levelProgress?: number;
}

interface RawRewardEvent {
  id: string;
  event_type?: string;
  eventType?: string;
  stars_earned?: number;
  starsEarned?: number;
  xp_earned?: number;
  xpEarned?: number;
  points?: number;
  source_type?: string | null;
  sourceType?: string | null;
  source_id?: string | null;
  sourceId?: string | null;
  created_at?: string;
  createdAt?: string;
}

interface RawLeaderboardEntry {
  student_id?: string;
  studentId?: string;
  student_name?: string;
  studentName?: string;
  full_name?: string;
  stars?: number;
  total_xp?: number;
  level: number;
  rank: number;
}

interface RawBadge {
  id?: string;
  code?: string;
  title_fr?: string | null;
  titleFr?: string | null;
  title_ar?: string | null;
  titleAr?: string | null;
  title_en?: string | null;
  titleEn?: string | null;
  title?: string | null;
  description_fr?: string | null;
  descriptionFr?: string | null;
  description_ar?: string | null;
  descriptionAr?: string | null;
  description_en?: string | null;
  descriptionEn?: string | null;
  icon?: string | null;
  criteria_type?: string;
  criteriaType?: string;
  criteria_value?: number;
  criteriaValue?: number;
  display_order?: number;
  displayOrder?: number;
  is_active?: boolean;
  isActive?: boolean;
}

interface RawBadgeReference {
  code?: string | null;
}

interface RawAwardRewardResponse extends RawStudentRewards {
  reward?: RawStudentRewards;
  newly_earned_badges?: Array<string | RawBadgeReference>;
  newlyEarnedBadges?: Array<string | RawBadgeReference>;
}

function calculateLevelProgress(raw: RawStudentRewards, xp: number): number {
  if (raw.levelProgress !== undefined || raw.level_progress !== undefined) {
    return raw.levelProgress ?? raw.level_progress ?? 0;
  }

  if (raw.next_level_xp && raw.next_level_xp > 0) {
    return Math.min(100, Math.round((xp / raw.next_level_xp) * 100));
  }

  return 0;
}

function normalizeStudentRewards(raw: RawStudentRewards): StudentRewards {
  const xp = raw.xp ?? raw.total_xp ?? 0;

  return {
    id: raw.id ?? raw.studentId ?? raw.student_id ?? '',
    studentId: raw.studentId ?? raw.student_id ?? '',
    stars: raw.stars ?? xp,
    xp,
    level: raw.level,
    streakDays: raw.streakDays ?? raw.streak_days ?? 0,
    longestStreak: raw.longestStreak ?? raw.longest_streak ?? 0,
    badges: raw.badges ?? raw.badge_ids ?? [],
    lastActivityAt:
      raw.lastActivityAt ?? raw.last_activity_at ?? raw.recent_events?.[0]?.created_at ?? null,
    levelProgress: calculateLevelProgress(raw, xp),
  };
}

function normalizeRewardEvent(raw: RawRewardEvent): RewardEvent {
  return {
    id: raw.id,
    eventType: raw.eventType ?? raw.event_type ?? '',
    starsEarned: raw.starsEarned ?? raw.stars_earned ?? raw.points ?? 0,
    xpEarned: raw.xpEarned ?? raw.xp_earned ?? raw.points ?? 0,
    sourceType: raw.sourceType ?? raw.source_type ?? null,
    sourceId: raw.sourceId ?? raw.source_id ?? null,
    createdAt: raw.createdAt ?? raw.created_at ?? '',
  };
}

function normalizeLeaderboardEntry(raw: RawLeaderboardEntry): LeaderboardEntry {
  return {
    studentId: raw.studentId ?? raw.student_id ?? '',
    studentName: raw.studentName ?? raw.student_name ?? raw.full_name ?? '',
    stars: raw.stars ?? raw.total_xp ?? 0,
    level: raw.level,
    rank: raw.rank,
  };
}

function normalizeBadge(raw: RawBadge): Badge {
  const fallbackTitle = raw.title ?? '';

  return {
    id: raw.id ?? raw.code ?? '',
    code: raw.code ?? '',
    titleFr: raw.titleFr ?? raw.title_fr ?? fallbackTitle,
    titleAr: raw.titleAr ?? raw.title_ar ?? fallbackTitle,
    titleEn: raw.titleEn ?? raw.title_en ?? fallbackTitle,
    descriptionFr: raw.descriptionFr ?? raw.description_fr ?? null,
    descriptionAr: raw.descriptionAr ?? raw.description_ar ?? null,
    descriptionEn: raw.descriptionEn ?? raw.description_en ?? null,
    icon: raw.icon ?? null,
    criteriaType: raw.criteriaType ?? raw.criteria_type ?? 'manual',
    criteriaValue: raw.criteriaValue ?? raw.criteria_value ?? 0,
    displayOrder: raw.displayOrder ?? raw.display_order ?? 0,
    isActive: raw.isActive ?? raw.is_active ?? true,
  };
}

function normalizeAwardRewardResponse(raw: RawAwardRewardResponse): AwardRewardResult {
  const rewardSource = raw.reward ?? raw;
  const newlyEarnedBadges = (raw.newly_earned_badges ?? raw.newlyEarnedBadges ?? [])
    .map((item) => (typeof item === 'string' ? item : (item.code ?? null)))
    .filter((item): item is string => Boolean(item));

  return {
    reward: normalizeStudentRewards(rewardSource),
    newly_earned_badges: newlyEarnedBadges,
  };
}

function serializeBadge(data: Partial<Badge>): Record<string, unknown> {
  const payload: Record<string, unknown> = {};

  if (data.id !== undefined) payload.id = data.id;
  if (data.code !== undefined) payload.code = data.code;
  if (data.titleFr !== undefined) payload.title_fr = data.titleFr;
  if (data.titleAr !== undefined) payload.title_ar = data.titleAr;
  if (data.titleEn !== undefined) payload.title_en = data.titleEn;
  if (data.descriptionFr !== undefined) payload.description_fr = data.descriptionFr;
  if (data.descriptionAr !== undefined) payload.description_ar = data.descriptionAr;
  if (data.descriptionEn !== undefined) payload.description_en = data.descriptionEn;
  if (data.icon !== undefined) payload.icon = data.icon;
  if (data.criteriaType !== undefined) payload.criteria_type = data.criteriaType;
  if (data.criteriaValue !== undefined) payload.criteria_value = data.criteriaValue;
  if (data.displayOrder !== undefined) payload.display_order = data.displayOrder;
  if (data.isActive !== undefined) payload.is_active = data.isActive;

  return payload;
}

export const rewardsService = {
  async getMyRewards(): Promise<StudentRewards> {
    const response = await api.get<RawStudentRewards>('/rewards/me');
    return normalizeStudentRewards(response.data);
  },

  async getStudentRewards(studentId: string): Promise<StudentRewards> {
    const response = await api.get<RawStudentRewards>(`/rewards/student/${studentId}`);
    return normalizeStudentRewards(response.data);
  },

  async getStudentHistory(studentId: string, limit?: number): Promise<RewardEvent[]> {
    const response = await api.list<RawRewardEvent>(
      `/rewards/student/${studentId}/history`,
      limit !== undefined ? { limit } : undefined,
    );

    return response.data.map(normalizeRewardEvent);
  },

  async getLeaderboard(classId: string, limit?: number): Promise<LeaderboardEntry[]> {
    const response = await api.list<RawLeaderboardEntry>(
      `/rewards/leaderboard/${classId}`,
      limit !== undefined ? { limit } : undefined,
    );

    return response.data.map(normalizeLeaderboardEntry);
  },

  async getBadges(): Promise<Badge[]> {
    const response = await api.list<RawBadge>('/rewards/badges');
    return response.data.map(normalizeBadge);
  },

  async createBadge(data: Partial<Badge>): Promise<Badge> {
    const response = await api.post<RawBadge>('/rewards/badges', serializeBadge(data));
    return normalizeBadge(response.data);
  },

  async updateBadge(badgeId: string, data: Partial<Badge>): Promise<Badge> {
    const response = await api.put<RawBadge>(`/rewards/badges/${badgeId}`, serializeBadge(data));
    return normalizeBadge(response.data);
  },

  async awardReward(data: AwardRewardPayload): Promise<AwardRewardResult> {
    const response = await api.post<RawAwardRewardResponse>('/rewards/award', data);
    return normalizeAwardRewardResponse(response.data);
  },
};

export function xpThresholdForLevel(level: number): number {
  if (level <= 1) {
    return 0;
  }

  return 50 * (level - 1) * level;
}
