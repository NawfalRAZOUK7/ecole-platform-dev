import { api } from '@/core/api/client';
import type {
  CreateQuestionPayload,
  DifficultyLevel,
  GenerateQuizParams,
  GeneratedQuiz,
  ImportFromQuizResponse,
  Question,
  QuestionBankStats,
  QuestionListParams,
  QuestionListResponse,
  QuestionType,
} from '@/entities/lms/question-bank/model/types';

type RawQuestionType = 'MCQ' | 'TRUE_FALSE' | 'FILL_IN' | 'DRAG_DROP' | 'MATCHING' | string;

interface RawQuestionBankItem {
  id: string;
  subject: string;
  difficulty: DifficultyLevel;
  question_type: RawQuestionType;
  question_data?: {
    question_text?: string;
    options?: unknown;
    correct_answer?: unknown;
  };
  tags?: string[];
  teacher_id?: string;
}

interface RawQuestionStatsItem {
  subject: string;
  difficulty: DifficultyLevel;
  question_count: number;
}

interface RawQuestionPage {
  items?: RawQuestionBankItem[];
  data?: RawQuestionBankItem[];
  total?: number;
  page?: number;
  page_size?: number;
}

type RawStatsObject = Partial<QuestionBankStats> & {
  total_questions?: number;
};

type QuestionListEnvelope = QuestionListResponse & {
  items: Question[];
};

function toBackendQuestionType(type: QuestionType): 'MCQ' | 'TRUE_FALSE' | 'FILL_IN' | 'MATCHING' {
  if (type === 'true_false') return 'TRUE_FALSE';
  if (type === 'short_answer') return 'FILL_IN';
  if (type === 'essay') return 'FILL_IN';
  return 'MCQ';
}

function toFrontendQuestionType(type: RawQuestionType): QuestionType {
  if (type === 'TRUE_FALSE') return 'true_false';
  if (type === 'FILL_IN') return 'short_answer';
  if (type === 'DRAG_DROP' || type === 'MATCHING') return 'essay';
  return 'mcq';
}

function normalizeChoices(options: unknown): Question['choices'] {
  if (!Array.isArray(options)) return [];
  return options.map((option, index) => {
    if (typeof option === 'string') {
      return { id: String(index + 1), text: option, is_correct: false };
    }
    if (option && typeof option === 'object') {
      const value = option as Record<string, unknown>;
      return {
        id: String(value.id ?? index + 1),
        text: String(value.text ?? value.label ?? ''),
        is_correct: Boolean(value.is_correct ?? value.correct),
      };
    }
    return { id: String(index + 1), text: String(option ?? ''), is_correct: false };
  });
}

function normalizeQuestion(item: RawQuestionBankItem): Question {
  return {
    id: item.id,
    subject: item.subject,
    type: toFrontendQuestionType(item.question_type),
    difficulty: item.difficulty,
    text: item.question_data?.question_text ?? '',
    choices: normalizeChoices(item.question_data?.options),
    correct_answer:
      item.question_data?.correct_answer == null ? null : String(item.question_data.correct_answer),
    tags: item.tags ?? [],
    created_by: item.teacher_id ?? '',
    created_at: '',
  };
}

function extractQuestionItems(data: RawQuestionBankItem[] | RawQuestionPage): {
  items: RawQuestionBankItem[];
  total?: number;
  page?: number;
  pageSize?: number;
} {
  if (Array.isArray(data)) {
    return { items: data };
  }

  return {
    items: data.items ?? data.data ?? [],
    total: data.total,
    page: data.page,
    pageSize: data.page_size,
  };
}

function shouldSerializeQuestion(payload: CreateQuestionPayload) {
  return Boolean(payload.subject && payload.difficulty && payload.text);
}

function serializeQuestion(payload: CreateQuestionPayload) {
  const questionType = toBackendQuestionType(payload.type);
  const choices = payload.choices ?? [];
  const correctChoice = choices.find((choice) => choice.is_correct);

  return {
    subject: payload.subject,
    difficulty: payload.difficulty,
    tags: payload.tags ?? [],
    question_data: {
      question_type: questionType,
      question_text: payload.text,
      options: choices.map((choice, index) => ({
        id: String(index + 1),
        text: choice.text,
        is_correct: choice.is_correct,
      })),
      correct_answer: payload.correct_answer ?? correctChoice?.text ?? '',
      points: 1,
    },
  };
}

export const questionBankService = {
  createQuestion(payload: CreateQuestionPayload) {
    return api.post<RawQuestionBankItem>(
      '/question-bank',
      shouldSerializeQuestion(payload) ? serializeQuestion(payload) : payload,
    );
  },

  async listQuestions(params?: QuestionListParams) {
    const response = await api.get<RawQuestionBankItem[] | RawQuestionPage>('/question-bank', {
      subject: params?.subject,
      type: params?.type,
      difficulty: params?.difficulty,
      page: params?.page,
      page_size: params?.page_size,
      limit: params?.page_size,
    });
    const page = extractQuestionItems(response.data);
    const questions = page.items.map(normalizeQuestion).filter((question) => {
      return params?.type ? question.type === params.type : true;
    });

    return {
      data: {
        items: questions,
        data: questions,
        total: page.total ?? questions.length,
        page: page.page ?? params?.page ?? 1,
        page_size: page.pageSize ?? params?.page_size ?? questions.length,
      } satisfies QuestionListEnvelope,
      meta: response.meta,
    };
  },

  importFromQuiz(quizId: string) {
    return api.post<ImportFromQuizResponse>(`/question-bank/import/${quizId}`, {});
  },

  generateQuiz(params: GenerateQuizParams) {
    return api.post<GeneratedQuiz>('/question-bank/generate-quiz', params);
  },

  async getStats() {
    const response = await api.get<RawQuestionStatsItem[] | RawStatsObject>('/question-bank/stats');
    if (!Array.isArray(response.data)) {
      const stats: QuestionBankStats & RawStatsObject = {
          ...response.data,
          total_questions: response.data.total_questions ?? response.data.total ?? 0,
          total: response.data.total ?? 0,
          by_subject: response.data.by_subject ?? {},
          by_type: response.data.by_type ?? {
            mcq: 0,
            true_false: 0,
            short_answer: 0,
            essay: 0,
          },
          by_difficulty: response.data.by_difficulty ?? {
            easy: 0,
            medium: 0,
            hard: 0,
          },
      };
      return { data: stats, meta: response.meta };
    }

    const stats: QuestionBankStats = {
      total: 0,
      by_subject: {},
      by_type: { mcq: 0, true_false: 0, short_answer: 0, essay: 0 },
      by_difficulty: { easy: 0, medium: 0, hard: 0 },
    };

    for (const item of response.data) {
      const count = item.question_count ?? 0;
      stats.total += count;
      stats.by_subject[item.subject] = (stats.by_subject[item.subject] ?? 0) + count;
      stats.by_difficulty[item.difficulty] =
        (stats.by_difficulty[item.difficulty] ?? 0) + count;
    }

    return { data: stats, meta: response.meta };
  },
};
