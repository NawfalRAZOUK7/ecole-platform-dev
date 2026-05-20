import { useInfiniteQuery, useQuery } from '@tanstack/react-query';
import { STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import { resultsService, type ResultsFilters } from '../api/results.api';

export const resultsQueryKeys = {
  all: ['results'] as const,
  assignments: (filters: Omit<ResultsFilters, 'cursor'>) =>
    [...resultsQueryKeys.all, 'assignments', filters] as const,
  quizzes: () => [...resultsQueryKeys.all, 'quizzes'] as const,
};

export function useAssignmentResults(filters: Omit<ResultsFilters, 'cursor'> = {}) {
  return useInfiniteQuery({
    queryKey: resultsQueryKeys.assignments(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      resultsService.listAssignmentResults({
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_RESULTS,
  });
}

export function useQuizAttemptResults() {
  return useQuery({
    queryKey: resultsQueryKeys.quizzes(),
    queryFn: async () => (await resultsService.listQuizResults()).data,
    staleTime: STALE_RESULTS,
  });
}
