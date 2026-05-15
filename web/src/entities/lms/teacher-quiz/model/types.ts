export interface QuestionInput {
  question_type: string;
  question_text: string;
  options: Record<string, unknown> | null;
  correct_answer: unknown;
  points: number;
  order: number;
  explanation: string;
}

export interface McqOptions {
  choices?: string[];
}

export interface TeacherQuizPayload extends Record<string, unknown> {
  title: string;
  description: string | null;
  subject: string | null;
  level_band: string | null;
  difficulty: string;
  time_limit_minutes: number | null;
  max_attempts: number;
  shuffle_questions: boolean;
  questions: QuestionInput[];
}

export type QuizManagerView = 'list' | 'create';

export const QUIZ_SUBJECTS = [
  'math',
  'french',
  'arabic',
  'science',
  'history',
  'geography',
  'english',
];

export const QUIZ_QUESTION_TYPES = ['mcq', 'true_false', 'fill_in_blank'];

export function createDefaultQuestion(type: string, order: number): QuestionInput {
  return {
    question_type: type,
    question_text: '',
    options: type === 'mcq' ? { choices: ['', ''] } : null,
    correct_answer: type === 'true_false' ? true : type === 'mcq' ? 0 : '',
    points: 1,
    order,
    explanation: '',
  };
}
