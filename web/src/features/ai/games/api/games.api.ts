import { api } from '@/core/api/client';

export const GAME_TYPES = ['memory_match', 'sorting', 'vocabulary_cards'] as const;
export const GAME_DIFFICULTIES = ['easy', 'medium', 'hard', 'expert'] as const;

export type GameType = (typeof GAME_TYPES)[number];
export type Difficulty = (typeof GAME_DIFFICULTIES)[number];

export interface GameConfig {
  id: string;
  gameType: GameType;
  title: string;
  titleAr: string | null;
  titleFr: string | null;
  subject: string | null;
  difficulty: Difficulty;
  targetAgeMin: number | null;
  targetAgeMax: number | null;
  config: Record<string, unknown>;
  rewardStars: number;
  rewardXp: number;
  schoolId: string | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface ListGameConfigsFilters {
  gameType?: GameType;
  difficulty?: Difficulty;
  subject?: string;
  targetAge?: number;
  isActive?: boolean;
  cursor?: string;
  limit?: number;
}

interface RawGameConfig {
  id: string;
  game_type?: string;
  gameType?: string;
  title: string;
  title_ar?: string | null;
  titleAr?: string | null;
  title_fr?: string | null;
  titleFr?: string | null;
  subject?: string | null;
  difficulty?: string;
  target_age_min?: number | null;
  targetAgeMin?: number | null;
  target_age_max?: number | null;
  targetAgeMax?: number | null;
  config?: Record<string, unknown>;
  reward_stars?: number;
  rewardStars?: number;
  reward_xp?: number;
  rewardXp?: number;
  school_id?: string | null;
  schoolId?: string | null;
  is_active?: boolean;
  isActive?: boolean;
  created_at?: string;
  createdAt?: string;
  updated_at?: string | null;
  updatedAt?: string | null;
}

function normalizeGameType(value: string | undefined): GameType {
  if (value && GAME_TYPES.includes(value as GameType)) {
    return value as GameType;
  }

  return 'memory_match';
}

function normalizeDifficulty(value: string | undefined): Difficulty {
  if (value && GAME_DIFFICULTIES.includes(value as Difficulty)) {
    return value as Difficulty;
  }

  return 'easy';
}

function normalizeGameConfig(raw: RawGameConfig): GameConfig {
  const createdAt = raw.createdAt ?? raw.created_at ?? '';

  return {
    id: raw.id,
    gameType: normalizeGameType(raw.gameType ?? raw.game_type),
    title: raw.title,
    titleAr: raw.titleAr ?? raw.title_ar ?? null,
    titleFr: raw.titleFr ?? raw.title_fr ?? null,
    subject: raw.subject ?? null,
    difficulty: normalizeDifficulty(raw.difficulty),
    targetAgeMin: raw.targetAgeMin ?? raw.target_age_min ?? null,
    targetAgeMax: raw.targetAgeMax ?? raw.target_age_max ?? null,
    config: raw.config ?? {},
    rewardStars: raw.rewardStars ?? raw.reward_stars ?? 0,
    rewardXp: raw.rewardXp ?? raw.reward_xp ?? 0,
    schoolId: raw.schoolId ?? raw.school_id ?? null,
    isActive: raw.isActive ?? raw.is_active ?? true,
    createdAt,
    updatedAt: raw.updatedAt ?? raw.updated_at ?? createdAt,
  };
}

function serializeGameConfig(data: Partial<GameConfig>): Record<string, unknown> {
  const payload: Record<string, unknown> = {};

  if (data.gameType !== undefined) payload.game_type = data.gameType;
  if (data.title !== undefined) payload.title = data.title;
  if (data.titleAr !== undefined) payload.title_ar = data.titleAr;
  if (data.titleFr !== undefined) payload.title_fr = data.titleFr;
  if (data.subject !== undefined) payload.subject = data.subject;
  if (data.difficulty !== undefined) payload.difficulty = data.difficulty;
  if (data.targetAgeMin !== undefined) payload.target_age_min = data.targetAgeMin;
  if (data.targetAgeMax !== undefined) payload.target_age_max = data.targetAgeMax;
  if (data.config !== undefined) payload.config = data.config;
  if (data.rewardStars !== undefined) payload.reward_stars = data.rewardStars;
  if (data.rewardXp !== undefined) payload.reward_xp = data.rewardXp;
  if (data.schoolId !== undefined) payload.school_id = data.schoolId;
  if (data.isActive !== undefined) payload.is_active = data.isActive;

  return payload;
}

export const gamesService = {
  async listConfigs(
    filters: ListGameConfigsFilters = {},
  ): Promise<{ items: GameConfig[]; nextCursor: string | null }> {
    const response = await api.list<RawGameConfig>('/games/configs', {
      game_type: filters.gameType,
      difficulty: filters.difficulty,
      subject: filters.subject,
      target_age: filters.targetAge,
      is_active: typeof filters.isActive === 'boolean' ? String(filters.isActive) : undefined,
      cursor: filters.cursor,
      limit: filters.limit,
    });

    return {
      items: response.data.map(normalizeGameConfig),
      nextCursor: response.meta.next_cursor,
    };
  },

  async getConfig(id: string): Promise<GameConfig> {
    const response = await api.get<RawGameConfig>(`/games/configs/${id}`);
    return normalizeGameConfig(response.data);
  },

  async createConfig(
    data: Omit<GameConfig, 'id' | 'createdAt' | 'updatedAt'>,
  ): Promise<GameConfig> {
    const response = await api.post<RawGameConfig>('/games/configs', serializeGameConfig(data));
    return normalizeGameConfig(response.data);
  },

  async updateConfig(id: string, data: Partial<GameConfig>): Promise<GameConfig> {
    const response = await api.put<RawGameConfig>(
      `/games/configs/${id}`,
      serializeGameConfig(data),
    );
    return normalizeGameConfig(response.data);
  },

  async completeConfig(
    id: string,
    payload: { score: number; timeSeconds: number },
  ): Promise<{ xpEarned: number; levelUp: boolean }> {
    const response = await api.post<{ xpEarned?: number; levelUp?: boolean }>(
      `/games/configs/${id}/complete`,
      { score: payload.score, time_seconds: payload.timeSeconds },
    );
    return {
      xpEarned: response.data.xpEarned ?? 0,
      levelUp: response.data.levelUp ?? false,
    };
  },
};
