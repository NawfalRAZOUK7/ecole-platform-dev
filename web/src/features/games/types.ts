export {
  GAME_DIFFICULTIES,
  GAME_TYPES,
  gamesService,
  type Difficulty,
  type GameConfig,
  type GameType,
  type ListGameConfigsFilters,
} from '@/services/games.service';

export interface MemoryMatchPair {
  front: string;
  back: string;
  image_url?: string | null;
}

export interface MemoryMatchConfig {
  pairs: MemoryMatchPair[];
  grid_cols: number;
  grid_rows: number;
  time_limit: number;
}

export interface SortingCategory {
  name: string;
  items: string[];
}

export interface SortingConfig {
  categories: SortingCategory[];
}

export interface VocabularyCard {
  word_ar: string;
  word_fr: string;
  image_url?: string | null;
  audio_url?: string | null;
}

export interface VocabularyCardsConfig {
  cards: VocabularyCard[];
}
