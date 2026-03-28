import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT, STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import { reportsService, type ReportHistoryFilters, type ReportType } from './reports.service';

export const reportsQueryKeys = {
  all: ['reports'] as const,
  options: (type: ReportType, classId: string) => [...reportsQueryKeys.all, 'options', type, classId] as const,
  history: (filters: Omit<ReportHistoryFilters, 'cursor'>) => [...reportsQueryKeys.all, 'history', filters] as const,
};

export function useReportOptions(type: ReportType, classId: string) {
  return useQuery({
    queryKey: reportsQueryKeys.options(type, classId),
    queryFn: async () => (await reportsService.getReportOptions(type, classId)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useReportHistory(filters: Omit<ReportHistoryFilters, 'cursor'>) {
  return useInfiniteQuery({
    queryKey: reportsQueryKeys.history(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      reportsService.listReportJobs({
        limit: 12,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_RESULTS,
  });
}

export function useGenerateReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => (await reportsService.generateReport(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: reportsQueryKeys.all });
    },
  });
}
