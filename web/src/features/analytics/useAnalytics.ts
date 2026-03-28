import { useMutation, useQuery } from '@tanstack/react-query';
import { STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import { analyticsService, type AnalyticsDashboardFilters, type ExportEntity } from './analytics.service';

export const analyticsQueryKeys = {
  all: ['analytics-dashboard'] as const,
  dashboard: (filters: AnalyticsDashboardFilters) => [...analyticsQueryKeys.all, 'dashboard', filters] as const,
};

export function useAnalyticsDashboard(filters: AnalyticsDashboardFilters) {
  return useQuery({
    queryKey: analyticsQueryKeys.dashboard(filters),
    queryFn: async () => analyticsService.getDashboard(filters),
    staleTime: STALE_RESULTS,
  });
}

export function useAnalyticsExport() {
  return useMutation({
    mutationFn: async ({
      format,
      entity,
      filters,
    }: {
      format: 'csv' | 'xlsx';
      entity: ExportEntity;
      filters: Record<string, string>;
    }) => analyticsService.downloadExport(format, entity, filters),
  });
}
