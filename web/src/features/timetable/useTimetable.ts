import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { timetableService } from './timetable.service';
import type {
  TimetableConstraints,
  TimetableExceptionCreatePayload,
  TimetableExceptionFilters,
  TimetableSlotBulkCreatePayload,
  TimetableSlotCreatePayload,
  TimetableSlotFilters,
  TimetableSlotUpdatePayload,
} from './timetable.service';

export const timetableQueryKeys = {
  all: ['timetable'] as const,
  classes: () => [...timetableQueryKeys.all, 'classes'] as const,
  weekly: (classId: string | null, isAdmin: boolean) =>
    [...timetableQueryKeys.all, 'weekly', isAdmin ? classId : 'me'] as const,
  slots: (filters: TimetableSlotFilters) => [...timetableQueryKeys.all, 'slots', filters] as const,
  exceptions: (filters: TimetableExceptionFilters) =>
    [...timetableQueryKeys.all, 'exceptions', filters] as const,
  constraints: () => [...timetableQueryKeys.all, 'constraints'] as const,
  generationJob: (jobId: string) => [...timetableQueryKeys.all, 'job', jobId] as const,
  generationPreview: (jobId: string) => [...timetableQueryKeys.all, 'preview', jobId] as const,
};

export function useTimetableClasses(enabled: boolean) {
  return useQuery({
    queryKey: timetableQueryKeys.classes(),
    queryFn: async () => (await timetableService.listClasses()).data,
    enabled,
    staleTime: STALE_DEFAULT,
  });
}

export function useWeeklyTimetable(classId: string | null, isAdmin: boolean) {
  return useQuery({
    queryKey: timetableQueryKeys.weekly(classId, isAdmin),
    queryFn: async () =>
      (await timetableService.getWeeklyTimetable(isAdmin ? classId || undefined : undefined)).data,
    enabled: !isAdmin || Boolean(classId),
    staleTime: STALE_DEFAULT,
  });
}

export function useTimetableSlots(filters: TimetableSlotFilters = {}, enabled = true) {
  return useQuery({
    queryKey: timetableQueryKeys.slots(filters),
    queryFn: async () => (await timetableService.listSlots(filters)).data,
    enabled,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateTimetableSlot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: TimetableSlotCreatePayload | TimetableSlotBulkCreatePayload) => {
      await timetableService.createSlot(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: timetableQueryKeys.all });
    },
  });
}

export function useUpdateTimetableSlot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      slotId,
      payload,
    }: {
      slotId: string;
      payload: TimetableSlotUpdatePayload;
    }) => {
      await timetableService.updateSlot(slotId, payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: timetableQueryKeys.all });
    },
  });
}

export function useDeleteTimetableSlot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (slotId: string) => {
      await timetableService.deleteSlot(slotId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: timetableQueryKeys.all });
    },
  });
}

export function useTimetableExceptions(filters: TimetableExceptionFilters = {}, enabled = true) {
  return useQuery({
    queryKey: timetableQueryKeys.exceptions(filters),
    queryFn: async () => (await timetableService.listExceptions(filters)).data,
    enabled,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateTimetableException() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: TimetableExceptionCreatePayload) => {
      await timetableService.createException(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: timetableQueryKeys.all });
    },
  });
}

export function useTimetableConstraints() {
  return useQuery({
    queryKey: timetableQueryKeys.constraints(),
    queryFn: async () => (await timetableService.getConstraints()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useSaveConstraints() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: TimetableConstraints) =>
      (await timetableService.saveConstraints(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: timetableQueryKeys.constraints() });
    },
  });
}

export function useTriggerGeneration() {
  return useMutation({
    mutationFn: async (academicYearId: string) =>
      (await timetableService.triggerGeneration({ academic_year_id: academicYearId })).data,
  });
}

export function useGenerationJob(jobId: string, enabled: boolean) {
  return useQuery({
    queryKey: timetableQueryKeys.generationJob(jobId),
    queryFn: async () => (await timetableService.getGenerationJob(jobId)).data,
    enabled: enabled && Boolean(jobId),
    staleTime: 0,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'pending' || status === 'running' ? 2000 : false;
    },
  });
}

export function useGenerationPreview(jobId: string, enabled: boolean) {
  return useQuery({
    queryKey: timetableQueryKeys.generationPreview(jobId),
    queryFn: async () => (await timetableService.getGenerationPreview(jobId)).data,
    enabled: enabled && Boolean(jobId),
    staleTime: STALE_DEFAULT,
  });
}

export function useApplyGeneration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (jobId: string) => (await timetableService.applyGeneration(jobId)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: timetableQueryKeys.all });
    },
  });
}
