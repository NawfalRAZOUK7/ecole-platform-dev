import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { questionBankService } from './question-bank.service';
import type { CreateQuestionPayload, GenerateQuizParams, QuestionListParams } from './question-bank.types';

export const questionBankQueryKeys = {
  all: ['question-bank'] as const,
  list: (params?: QuestionListParams) => [...questionBankQueryKeys.all, 'list', params ?? {}] as const,
  stats: () => [...questionBankQueryKeys.all, 'stats'] as const,
};

export function useQuestions(params?: QuestionListParams) {
  return useQuery({
    queryKey: questionBankQueryKeys.list(params),
    queryFn: async () => (await questionBankService.listQuestions(params)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useQuestionBankStats() {
  return useQuery({
    queryKey: questionBankQueryKeys.stats(),
    queryFn: async () => (await questionBankService.getStats()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateQuestion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateQuestionPayload) =>
      (await questionBankService.createQuestion(payload)).data,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: questionBankQueryKeys.all }),
      ]);
    },
  });
}

export function useImportFromQuiz() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (quizId: string) =>
      (await questionBankService.importFromQuiz(quizId)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: questionBankQueryKeys.all });
    },
  });
}

export function useGenerateQuiz() {
  return useMutation({
    mutationFn: async (params: GenerateQuizParams) =>
      (await questionBankService.generateQuiz(params)).data,
  });
}
