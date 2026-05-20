import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { attendanceService } from '../api/attendance.api';
import type {
  AttendanceRecord,
  BulkAttendancePayload,
  JustificationMutationInput,
  JustificationPayload,
  JustificationReviewPayload,
} from '../model/attendance.types';

export const attendanceQueryKeys = {
  all: ['attendance'] as const,
  classAttendance: (classId: string, date: string) =>
    [...attendanceQueryKeys.all, 'class', classId, date] as const,
  trends: (classId: string, from: string, to: string) =>
    [...attendanceQueryKeys.all, 'trends', classId, from, to] as const,
  alerts: (schoolId: string, programId?: string) =>
    [...attendanceQueryKeys.all, 'alerts', schoolId, programId ?? 'all'] as const,
  studentHistory: (studentId: string) =>
    [...attendanceQueryKeys.all, 'student', studentId] as const,
};

function mergeAttendanceRecords(
  current: AttendanceRecord[] | undefined,
  payload: BulkAttendancePayload,
) {
  const currentMap = new Map((current ?? []).map((record) => [record.student_id, record]));

  return payload.records.map((record, index) => {
    const existing = currentMap.get(record.student_id);
    return {
      id: existing?.id ?? `${payload.class_id}-${payload.date}-${record.student_id}`,
      student_id: record.student_id,
      student_name: existing?.student_name ?? `Student ${index + 1}`,
      class_id: payload.class_id,
      date: payload.date,
      status: record.status,
      justified: existing?.justified ?? false,
      justification: record.note ?? existing?.justification,
      marked_by: existing?.marked_by ?? 'current-user',
    } satisfies AttendanceRecord;
  });
}

export function useClassAttendance(classId: string, date: string) {
  return useQuery({
    queryKey: attendanceQueryKeys.classAttendance(classId, date),
    queryFn: async () => (await attendanceService.getClassAttendance(classId, date)).data.records,
    enabled: Boolean(classId && date),
    staleTime: STALE_DEFAULT,
  });
}

export function useMarkAttendance() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: BulkAttendancePayload) => {
      await attendanceService.markAttendance(payload);
      return payload;
    },
    onMutate: async (payload) => {
      const queryKey = attendanceQueryKeys.classAttendance(payload.class_id, payload.date);
      await queryClient.cancelQueries({ queryKey });
      const previous = queryClient.getQueryData<AttendanceRecord[]>(queryKey);
      queryClient.setQueryData<AttendanceRecord[]>(
        queryKey,
        mergeAttendanceRecords(previous, payload),
      );
      return { previous, queryKey };
    },
    onError: (_error, _payload, context) => {
      if (context?.previous) {
        queryClient.setQueryData(context.queryKey, context.previous);
      }
    },
    onSuccess: async (_data, payload) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: attendanceQueryKeys.classAttendance(payload.class_id, payload.date),
        }),
        queryClient.invalidateQueries({ queryKey: [...attendanceQueryKeys.all, 'trends'] }),
        queryClient.invalidateQueries({ queryKey: [...attendanceQueryKeys.all, 'alerts'] }),
      ]);
    },
  });
}

export function useSubmitJustification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ recordId, justification, file }: JustificationMutationInput) => {
      await attendanceService.submitJustification(recordId, justification, file);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: attendanceQueryKeys.all });
    },
  });
}

export function useAttendanceTrends(classId: string, dateRange: { from: string; to: string }) {
  return useQuery({
    queryKey: attendanceQueryKeys.trends(classId, dateRange.from, dateRange.to),
    queryFn: async () =>
      (await attendanceService.getAttendanceTrends(classId, dateRange.from, dateRange.to)).data,
    enabled: Boolean(classId && dateRange.from && dateRange.to),
    staleTime: STALE_DEFAULT,
  });
}

export function useAttendanceAlerts(schoolId: string, programId?: string) {
  return useQuery({
    queryKey: attendanceQueryKeys.alerts(schoolId, programId),
    queryFn: async () => (await attendanceService.getAttendanceAlerts(schoolId, programId)).data,
    enabled: Boolean(schoolId),
    staleTime: STALE_DEFAULT,
  });
}

export function useStudentHistory(studentId: string) {
  return useQuery({
    queryKey: attendanceQueryKeys.studentHistory(studentId),
    queryFn: async () => (await attendanceService.getStudentHistory(studentId)).data,
    enabled: Boolean(studentId),
    staleTime: STALE_DEFAULT,
  });
}

export function useSubmitJustificationDirect() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: JustificationPayload) =>
      attendanceService.submitJustificationDirect(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: attendanceQueryKeys.all });
    },
  });
}

export function useReviewJustification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      justificationId,
      payload,
    }: {
      justificationId: string;
      payload: JustificationReviewPayload;
    }) => attendanceService.reviewJustification(justificationId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: attendanceQueryKeys.all });
    },
  });
}

export function useCheckAttendanceThresholds() {
  return useMutation({
    mutationFn: async () => (await attendanceService.checkThresholds()).data,
  });
}
