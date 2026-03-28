import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { timetableService } from './timetable.service';

export const timetableQueryKeys = {
  all: ['timetable'] as const,
  classes: () => [...timetableQueryKeys.all, 'classes'] as const,
  weekly: (classId: string | null, isAdmin: boolean) => [...timetableQueryKeys.all, 'weekly', isAdmin ? classId : 'me'] as const,
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
    queryFn: async () => (await timetableService.getWeeklyTimetable(isAdmin ? classId || undefined : undefined)).data,
    enabled: !isAdmin || Boolean(classId),
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateTimetableSlot() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
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
    mutationFn: async ({ slotId, payload }: { slotId: string; payload: Record<string, unknown> }) => {
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

export function useCreateTimetableException() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: Record<string, unknown>) => {
      await timetableService.createException(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: timetableQueryKeys.all });
    },
  });
}
