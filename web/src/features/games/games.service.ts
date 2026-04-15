import { api } from '@/services/api/client';

export const GAME_TYPES = ['memory_match', 'sorting', 'vocabulary_cards'] as const;
export const GAME_DIFFICULTIES = ['easy', 'medium', 'hard'] as const;

export type GameType = (typeof GAME_TYPES)[number];
export type GameDifficulty = (typeof GAME_DIFFICULTIES)[number];

export interface GameConfig {
  id: string;
  game_type: string;
  title: string;
  title_ar: string | null;
  title_fr: string | null;
  subject: string | null;
  difficulty: string;
  target_age_min: number | null;
  target_age_max: number | null;
  config: Record<string, unknown>;
  reward_stars: number;
  reward_xp: number;
  school_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface GameConfigFilters extends Record<string, boolean | number | string | undefined> {
  cursor?: string;
  game_type?: string;
  difficulty?: string;
  subject?: string;
  target_age?: number;
  is_active?: boolean;
}

export interface GameConfigPayload {
  game_type: string;
  title: string;
  title_ar?: string | null;
  title_fr?: string | null;
  subject?: string | null;
  difficulty: string;
  target_age_min?: number | null;
  target_age_max?: number | null;
  config: Record<string, unknown>;
  reward_stars: number;
  reward_xp: number;
  is_active: boolean;
}

export const gamesService = {
  listConfigs(params: GameConfigFilters) {
    const requestParams: Record<string, string | number | undefined> = {
      cursor: params.cursor,
      game_type: params.game_type,
      difficulty: params.difficulty,
      subject: params.subject,
      target_age: params.target_age,
      is_active: typeof params.is_active === 'boolean' ? String(params.is_active) : undefined,
    };

    return api.list<GameConfig>('/games/configs', requestParams);
  },

  getConfig(gameId: string) {
    return api.get<GameConfig>(`/games/configs/${gameId}`);
  },

  createConfig(payload: GameConfigPayload) {
    return api.post<GameConfig>('/games/configs', payload);
  },

  updateConfig(gameId: string, payload: Partial<GameConfigPayload>) {
    return api.put<GameConfig>(`/games/configs/${gameId}`, payload);
  },
};
