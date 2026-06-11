export {
  GAME_DIFFICULTIES,
  GAME_TYPES,
  gamesService,
  type Difficulty,
  type GameConfig,
  type GameType,
  type ListGameConfigsFilters,
} from '@/features/ai/games/api/games.api';

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

/** One puzzle piece: a word starting with the target letter, with an emoji
 *  and an optional image (image_url takes priority, emoji is the fallback). */
export interface LetterPuzzlePiece {
  word: string;
  emoji?: string | null;
  image_url?: string | null;
  audio_url?: string | null;
}

export interface LetterPuzzleConfig {
  letter: string;
  language: 'ar' | 'fr' | 'en';
  letter_audio_url?: string | null;
  grid?: { rows: number; cols: number };
  pieces: LetterPuzzlePiece[];
}
