export type QuestionType = 'mcq' | 'true_false' | 'short_answer' | 'essay';
export type DifficultyLevel = 'easy' | 'medium' | 'hard';

export interface QuestionChoice {
  id: string;
  text: string;
  is_correct: boolean;
}

export interface Question {
  id: string;
  subject: string;
  type: QuestionType;
  difficulty: DifficultyLevel;
  text: string;
  choices: QuestionChoice[];
  correct_answer: string | null;
  tags: string[];
  created_by: string;
  created_at: string;
}

export interface CreateQuestionPayload {
  subject: string;
  type: QuestionType;
  difficulty: DifficultyLevel;
  text: string;
  choices?: Omit<QuestionChoice, 'id'>[];
  correct_answer?: string | null;
  tags?: string[];
}

export interface QuestionListParams {
  subject?: string;
  type?: QuestionType;
  difficulty?: DifficultyLevel;
  page?: number;
  page_size?: number;
}

export interface QuestionListResponse {
  data: Question[];
  total: number;
  page: number;
  page_size: number;
}

export interface ImportFromQuizResponse {
  imported: number;
  skipped: number;
  questions: Question[];
}

export interface GenerateQuizParams {
  subject: string;
  difficulty?: DifficultyLevel;
  count: number;
  tags?: string[];
}

export interface GeneratedQuiz {
  questions: Question[];
  total: number;
}

export interface QuestionBankStats {
  total: number;
  by_subject: Record<string, number>;
  by_type: Record<QuestionType, number>;
  by_difficulty: Record<DifficultyLevel, number>;
}
