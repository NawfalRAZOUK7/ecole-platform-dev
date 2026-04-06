import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { financialHealthService } from './financial-health.service';
import type {
  ComputeCashflowPayload,
  ComputeCostPerStudentPayload,
  ComputeFinancialSnapshotPayload,
  ComputeRetentionPayload,
} from './financial-health.types';

export const financialHealthQueryKeys = {
  all: ['financial-health'] as const,
  retention: (filters: { skip?: number; limit?: number }) =>
    [...financialHealthQueryKeys.all, 'retention', filters] as const,
  cashflow: (filters: { start_month?: string; end_month?: string; skip?: number; limit?: number }) =>
    [...financialHealthQueryKeys.all, 'cashflow', filters] as const,
  cost: (academicYearId: string) => [...financialHealthQueryKeys.all, 'cost', academicYearId] as const,
  snapshot: (snapshotDate?: string) => [...financialHealthQueryKeys.all, 'snapshot', snapshotDate || 'latest'] as const,
  dashboard: () => [...financialHealthQueryKeys.all, 'dashboard'] as const,
  trends: (months: number) => [...financialHealthQueryKeys.all, 'trends', months] as const,
};

export function useFinancialRetentionMetrics(params: {
  skip?: number;
  limit?: number;
} = {}) {
  return useQuery({
    queryKey: financialHealthQueryKeys.retention(params),
    queryFn: async () => (await financialHealthService.listRetentionMetrics(params)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useComputeRetentionMetric() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ComputeRetentionPayload) => financialHealthService.computeRetention(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: financialHealthQueryKeys.all });
    },
  });
}

export function useFinancialCashflowForecasts(params: {
  start_month?: string;
  end_month?: string;
  skip?: number;
  limit?: number;
} = {}) {
  return useQuery({
    queryKey: financialHealthQueryKeys.cashflow(params),
    queryFn: async () => (await financialHealthService.listCashflowForecasts(params)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useComputeCashflowForecast() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ComputeCashflowPayload) => financialHealthService.computeCashflow(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: financialHealthQueryKeys.all });
    },
  });
}

export function useFinancialCostPerStudent(academicYearId: string) {
  return useQuery({
    queryKey: financialHealthQueryKeys.cost(academicYearId),
    queryFn: async () => (await financialHealthService.getCostPerStudent(academicYearId)).data,
    enabled: Boolean(academicYearId),
    staleTime: STALE_DEFAULT,
  });
}

export function useComputeCostPerStudent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ComputeCostPerStudentPayload) => financialHealthService.computeCostPerStudent(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: financialHealthQueryKeys.all });
    },
  });
}

export function useFinancialSnapshot(snapshotDate?: string) {
  return useQuery({
    queryKey: financialHealthQueryKeys.snapshot(snapshotDate),
    queryFn: async () => (await financialHealthService.getSnapshot(snapshotDate)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useComputeFinancialSnapshot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: ComputeFinancialSnapshotPayload) => financialHealthService.computeSnapshot(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: financialHealthQueryKeys.all });
    },
  });
}

export function useFinancialDashboard() {
  return useQuery({
    queryKey: financialHealthQueryKeys.dashboard(),
    queryFn: async () => (await financialHealthService.getDashboard()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useFinancialTrends(months = 12) {
  return useQuery({
    queryKey: financialHealthQueryKeys.trends(months),
    queryFn: async () => (await financialHealthService.getTrends(months)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useFinancialExport() {
  return useMutation({
    mutationFn: async (format: 'csv' | 'pdf') =>
      format === 'pdf' ? financialHealthService.exportPdf() : financialHealthService.exportCsv(),
  });
}
