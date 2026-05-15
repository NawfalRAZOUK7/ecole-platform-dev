import { api } from '@/core/api/client';
import type {
  CreateQuestionPayload,
  GenerateQuizParams,
  GeneratedQuiz,
  ImportFromQuizResponse,
  Question,
  QuestionBankStats,
  QuestionListParams,
  QuestionListResponse,
} from '@/entities/lms/question-bank/model/types';

export const questionBankService = {
  createQuestion(payload: CreateQuestionPayload) {
    return api.post<Question>('/question-bank', payload);
  },

  listQuestions(params?: QuestionListParams) {
    const query = new URLSearchParams();
    if (params?.subject) query.set('subject', params.subject);
    if (params?.type) query.set('type', params.type);
    if (params?.difficulty) query.set('difficulty', params.difficulty);
    if (params?.page != null) query.set('page', String(params.page));
    if (params?.page_size != null) query.set('page_size', String(params.page_size));
    const qs = query.toString();
    return api.get<QuestionListResponse>(`/question-bank${qs ? `?${qs}` : ''}`);
  },

  importFromQuiz(quizId: string) {
    return api.post<ImportFromQuizResponse>(`/question-bank/import/${quizId}`, {});
  },

  generateQuiz(params: GenerateQuizParams) {
    return api.post<GeneratedQuiz>('/question-bank/generate-quiz', params);
  },

  getStats() {
    return api.get<QuestionBankStats>('/question-bank/stats');
  },
};
