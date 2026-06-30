/**
 * Single source of truth for curriculum vocabulary.
 *
 * Mirrors the backend enums in `backend/app/models/taxonomy.py`
 * (`ContentLevelBand`, `ContentSubject`). The backend rejects any value outside
 * these sets, so every level/subject dropdown in the app MUST draw from here.
 * Keep in sync with the backend enums.
 */

// Niveaux officiels marocains (MEN). Stored value = the code; the FR equivalent
// is shown via LEVEL_LABELS for readability.
export const LEVEL_BANDS: readonly string[] = [
  'PS',
  'MS',
  'GS',
  '1AEP',
  '2AEP',
  '3AEP',
  '4AEP',
  '5AEP',
  '6AEP',
  '1AC',
  '2AC',
  '3AC',
  'TC',
  '1BAC',
  '2BAC',
];

// FR display hints for the Moroccan codes (optional — UIs may also use i18n).
export const LEVEL_LABELS: Record<string, string> = {
  PS: 'PS (Petite section)',
  MS: 'MS (Moyenne section)',
  GS: 'GS (Grande section)',
  '1AEP': '1AEP (CP)',
  '2AEP': '2AEP (CE1)',
  '3AEP': '3AEP (CE2)',
  '4AEP': '4AEP (CM1)',
  '5AEP': '5AEP (CM2)',
  '6AEP': '6AEP',
  '1AC': '1AC (6ème)',
  '2AC': '2AC (5ème/4ème)',
  '3AC': '3AC (3ème)',
  TC: 'Tronc commun (2nde)',
  '1BAC': '1BAC (1ère)',
  '2BAC': '2BAC (Terminale)',
};

// Matières officielles. 'other' is the escape hatch — when chosen, the user
// supplies a free-text name via the `subject_other` field.
// NOTE: keep in sync with the backend `ContentSubject` enum — verified by
// `scripts/check-taxonomy-sync.mjs`.
export const SUBJECTS: readonly string[] = [
  'arabic',
  'french',
  'english',
  'amazigh',
  'math',
  'activite_scientifique',
  'svt',
  'physique_chimie',
  'histoire_geo',
  'civic',
  'philosophy',
  'islamic',
  'quranic',
  'art',
  'music',
  'sport',
  'informatique',
  'technology',
  'economics',
  'accounting',
  'arabic_letters',
  'literacy',
  'vocabulary',
  'pedagogy',
  'other',
];

// Academic-core subset offered when authoring quizzes (all valid backend enum
// members, so creation always passes validation).
export const QUIZ_SUBJECTS: readonly string[] = [
  'arabic',
  'french',
  'english',
  'math',
  'activite_scientifique',
  'svt',
  'physique_chimie',
  'histoire_geo',
  'islamic',
  'philosophy',
];

// Sentinel for the free-text subject path.
export const SUBJECT_OTHER = 'other';
