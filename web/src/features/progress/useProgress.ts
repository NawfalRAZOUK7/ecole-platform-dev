import { useQuery } from '@tanstack/react-query';
import { STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import { progressService } from './progress.service';

export const progressQueryKeys = {
  all: ['progress'] as const,
  dashboard: (studentId: string | null) => [...progressQueryKeys.all, 'dashboard', studentId] as const,
  children: () => [...progressQueryKeys.all, 'children'] as const,
};

export function useProgressDashboard(studentId: string | null) {
  return useQuery({
    queryKey: progressQueryKeys.dashboard(studentId),
    queryFn: async () => (await progressService.getProgress(studentId)).data.data,
    staleTime: STALE_RESULTS,
  });
}

export function useChildrenProgressOverview() {
  return useQuery({
    queryKey: progressQueryKeys.children(),
    queryFn: async () => (await progressService.getChildrenOverview()).data.data,
    staleTime: STALE_RESULTS,
  });
}
