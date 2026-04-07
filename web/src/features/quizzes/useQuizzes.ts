import { useQuery } from '@tanstack/react-query';
import { STALE_DEFAULT, STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import { quizzesService } from './quizzes.service';

export const quizzesQueryKeys = {
  all: ['quizzes'] as const,
  detail: (quizId: string | null | undefined) => [...quizzesQueryKeys.all, 'detail', quizId] as const,
  analytics: (quizId: string | null | undefined) => [...quizzesQueryKeys.all, 'analytics', quizId] as const,
  results: (attemptId: string | null | undefined) => [...quizzesQueryKeys.all, 'results', attemptId] as const,
};

export function useQuizDetail(quizId: string | null | undefined) {
  return useQuery({
    queryKey: quizzesQueryKeys.detail(quizId),
    queryFn: async () => (await quizzesService.getQuiz(quizId!)).data,
    enabled: Boolean(quizId),
    staleTime: STALE_DEFAULT,
  });
}

export function useQuizAnalytics(quizId: string | null | undefined) {
  return useQuery({
    queryKey: quizzesQueryKeys.analytics(quizId),
    queryFn: async () => (await quizzesService.getAnalytics(quizId!)).data,
    enabled: Boolean(quizId),
    staleTime: STALE_RESULTS,
  });
}

export function useQuizResults(attemptId: string | null | undefined) {
  return useQuery({
    queryKey: quizzesQueryKeys.results(attemptId),
    queryFn: async () => (await quizzesService.getResults(attemptId!)).data,
    enabled: Boolean(attemptId),
    staleTime: STALE_RESULTS,
  });
}
