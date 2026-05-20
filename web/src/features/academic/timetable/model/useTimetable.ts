import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { timetableService } from '../api/timetable.api';
import type {
  TimetableConstraints,
  TimetableExceptionCreatePayload,
  TimetableExceptionFilters,
  TimetableSlotBulkCreatePayload,
  TimetableSlotCreatePayload,
  TimetableSlotFilters,
  TimetableSlotUpdatePayload,
} from '../api/timetable.api';

export const timetableQueryKeys = {
  all: ['timetable'] as const,
  classes: () => [...timetableQueryKeys.all, 'classes'] as const,
  weekly: (classId: string | null, isAdmin: boolean) =>
    [...timetableQueryKeys.all, 'weekly', isAdmin ? classId : 'me'] as const,
  classWeekly: (classId: string) => [...timetableQueryKeys.all, 'class-weekly', classId] as const,
  teacherWeekly: (teacherId: string) =>
    [...timetableQueryKeys.all, 'teacher-weekly', teacherId] as const,
  myWeekly: () => [...timetableQueryKeys.all, 'my-weekly'] as const,
  slots: (filters: TimetableSlotFilters) => [...timetableQueryKeys.all, 'slots', filters] as const,
  exceptions: (filters: TimetableExceptionFilters) =>
    [...timetableQueryKeys.all, 'exceptions', filters] as const,
  constraints: (academicYearId: string) =>
    [...timetableQueryKeys.all, 'constraints', academicYearId] as const,
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

export function useTimetableConstraints(academicYearId: string) {
  return useQuery({
    queryKey: timetableQueryKeys.constraints(academicYearId),
    queryFn: async () => (await timetableService.getConstraints(academicYearId)).data,
    enabled: Boolean(academicYearId),
    staleTime: STALE_DEFAULT,
  });
}

export function useSaveConstraints() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: TimetableConstraints) =>
      (await timetableService.saveConstraints(payload)).data,
    onSuccess: async (data) => {
      queryClient.setQueryData(timetableQueryKeys.constraints(data.academic_year_id), data);
      await queryClient.invalidateQueries({
        queryKey: timetableQueryKeys.constraints(data.academic_year_id),
      });
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

export function useClassWeeklyTimetable(classId: string, enabled = true) {
  return useQuery({
    queryKey: timetableQueryKeys.classWeekly(classId),
    queryFn: async () => (await timetableService.getClassWeekly(classId)).data,
    enabled: enabled && Boolean(classId),
    staleTime: STALE_DEFAULT,
  });
}

export function useTeacherWeeklyTimetable(teacherId: string, enabled = true) {
  return useQuery({
    queryKey: timetableQueryKeys.teacherWeekly(teacherId),
    queryFn: async () => (await timetableService.getTeacherWeekly(teacherId)).data,
    enabled: enabled && Boolean(teacherId),
    staleTime: STALE_DEFAULT,
  });
}

export function useMyWeeklyTimetable() {
  return useQuery({
    queryKey: timetableQueryKeys.myWeekly(),
    queryFn: async () => (await timetableService.getMyWeekly()).data,
    staleTime: STALE_DEFAULT,
  });
}
