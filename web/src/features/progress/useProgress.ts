import { useQuery } from '@tanstack/react-query';
import { STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import { progressService } from './progress.service';

export const progressQueryKeys = {
  all: ['progress'] as const,
  dashboard: (studentId: string | null) =>
    [...progressQueryKeys.all, 'dashboard', studentId] as const,
  children: () => [...progressQueryKeys.all, 'children'] as const,
};

export function useProgressDashboard(studentId: string | null) {
  return useQuery({
    queryKey: progressQueryKeys.dashboard(studentId),
    queryFn: async () => {
      const r = await progressService.getProgress(studentId);
      return r?.data?.data ?? null;
    },
    staleTime: STALE_RESULTS,
  });
}

export function useChildrenProgressOverview() {
  return useQuery({
    queryKey: progressQueryKeys.children(),
    queryFn: async () => {
      const r = await progressService.getChildrenOverview();
      return r?.data?.data ?? null;
    },
    staleTime: STALE_RESULTS,
  });
}

export function useStudentProgress(studentId: string) {
  return useQuery({
    queryKey: progressQueryKeys.dashboard(studentId),
    queryFn: async () => {
      const r = await progressService.getStudentProgress(studentId);
      return r?.data?.data ?? null;
    },
    enabled: Boolean(studentId),
    staleTime: STALE_RESULTS,
  });
}

export function useMyProgress() {
  return useQuery({
    queryKey: progressQueryKeys.dashboard(null),
    queryFn: async () => {
      const r = await progressService.getMyProgress();
      return r?.data?.data ?? null;
    },
    staleTime: STALE_RESULTS,
  });
}
