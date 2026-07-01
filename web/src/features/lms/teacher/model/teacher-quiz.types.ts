import type { QuestionInput } from '@/features/lms/teacher/api/teacher.api';

export interface McqOptions {
  choices?: string[];
}

export interface TeacherQuizPayload extends Record<string, unknown> {
  title: string;
  description: string | null;
  subject: string | null;
  /** Free-text matière name; required by the backend when subject === 'other'. */
  subject_other: string | null;
  level_band: string | null;
  difficulty: string;
  time_limit_minutes: number | null;
  max_attempts: number;
  shuffle_questions: boolean;
  questions: QuestionInput[];
}

export type QuizManagerView = 'list' | 'create';

// Curriculum vocabulary — single source of truth (mirrors backend enums).
export { QUIZ_SUBJECTS, SUBJECT_OTHER } from '@/shared/taxonomy';
import { QUIZ_SUBJECTS, SUBJECT_OTHER } from '@/shared/taxonomy';

/** Quiz subject dropdown options: academic matières + the 'other' escape hatch
 *  (which reveals a free-text `subject_other` input). */
export const QUIZ_SUBJECT_OPTIONS: readonly string[] = [...QUIZ_SUBJECTS, SUBJECT_OTHER];

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
