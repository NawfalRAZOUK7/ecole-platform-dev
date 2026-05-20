import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT, STALE_RESULTS } from '@/shared/hooks/useQueryDefaults';
import {
  reportsService,
  type CreateSchedulePayload,
  type ReportHistoryFilters,
  type ReportType,
  type UpdateSchedulePayload,
} from '../api/reports.api';

export const reportsQueryKeys = {
  all: ['reports'] as const,
  options: (type: ReportType, classId: string) =>
    [...reportsQueryKeys.all, 'options', type, classId] as const,
  history: (filters: Omit<ReportHistoryFilters, 'cursor'>) =>
    [...reportsQueryKeys.all, 'history', filters] as const,
  schedules: () => [...reportsQueryKeys.all, 'schedules'] as const,
  jobStatus: (jobId: string) => [...reportsQueryKeys.all, 'job', jobId] as const,
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
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_RESULTS,
  });
}

export function useGenerateReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) =>
      (await reportsService.generateReport(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: reportsQueryKeys.all });
    },
  });
}

export function useReportSchedules() {
  return useQuery({
    queryKey: reportsQueryKeys.schedules(),
    queryFn: async () => (await reportsService.listSchedules()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateReportSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateSchedulePayload) =>
      (await reportsService.createSchedule(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: reportsQueryKeys.schedules() });
    },
  });
}

export function useUpdateReportSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      scheduleId,
      payload,
    }: {
      scheduleId: string;
      payload: UpdateSchedulePayload;
    }) => (await reportsService.updateSchedule(scheduleId, payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: reportsQueryKeys.schedules() });
    },
  });
}

export function useDeleteReportSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (scheduleId: string) => {
      await reportsService.deleteSchedule(scheduleId);
      return scheduleId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: reportsQueryKeys.schedules() });
    },
  });
}

export function useRunReportSchedule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (scheduleId: string) => (await reportsService.runSchedule(scheduleId)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: reportsQueryKeys.all });
    },
  });
}

export function useReportJobStatus(jobId: string, enabled: boolean) {
  return useQuery({
    queryKey: reportsQueryKeys.jobStatus(jobId),
    queryFn: async () => (await reportsService.getJobStatus(jobId)).data,
    enabled: enabled && Boolean(jobId),
    staleTime: 0,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'pending' || status === 'generating' ? 3000 : false;
    },
  });
}

export function useDownloadReport() {
  return useMutation({
    mutationFn: async (jobId: string) => (await reportsService.downloadReport(jobId)).data,
  });
}
