export type QuestionType = 'MCQ' | 'TRUE_FALSE' | 'FILL_IN' | 'DRAG_DROP' | 'MATCHING';

export interface McqOption {
  id: string;
  text: string;
}

export interface DragDropItem {
  id: string;
  text: string;
}

export interface MatchingPair {
  id: string;
  text: string;
}

export interface Question {
  _key: string;
  question_type: QuestionType;
  question_text: string;
  options: unknown;
  correct_answer: unknown;
  points: number;
  order: number;
  explanation: string;
}

export const QUESTION_TYPES: QuestionType[] = ['MCQ', 'TRUE_FALSE', 'FILL_IN', 'DRAG_DROP', 'MATCHING'];
export const SUBJECTS = ['math', 'french', 'arabic', 'science', 'history', 'geography', 'english'];
export const LEVELS = ['maternelle', 'cp', 'ce1', 'ce2', 'cm1', 'cm2', '6eme', '5eme', '4eme', '3eme', '2nde', '1ere', 'terminale'];

let keyCounter = 0;

export function nextKey() {
  return `q_${++keyCounter}`;
}

export function defaultQuestion(type: QuestionType, order: number): Question {
  const base = { _key: nextKey(), question_type: type, question_text: '', points: 1, order, explanation: '' };

  switch (type) {
    case 'MCQ':
      return { ...base, options: [{ id: 'a', text: '' }, { id: 'b', text: '' }], correct_answer: [] };
    case 'TRUE_FALSE':
      return { ...base, options: null, correct_answer: true };
    case 'FILL_IN':
      return { ...base, options: null, correct_answer: [''] };
    case 'DRAG_DROP':
      return { ...base, options: { items: [{ id: 'i1', text: '' }], zones: [{ id: 'z1', text: '' }] }, correct_answer: {} };
    case 'MATCHING':
      return { ...base, options: { left: [{ id: 'l1', text: '' }], right: [{ id: 'r1', text: '' }] }, correct_answer: {} };
  }
}
