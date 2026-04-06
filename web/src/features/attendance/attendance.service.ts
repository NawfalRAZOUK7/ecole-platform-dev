import { api } from '@/services/api/client';
import type {
  AttendanceAlert,
  AttendanceClassStats,
  AttendanceExportResponse,
  AttendanceRecord,
  AttendanceTrend,
  BulkAttendancePayload,
  Justification,
  JustificationPayload,
  JustificationReviewPayload,
} from './attendance.types';

export const attendanceService = {
  getClassAttendance(classId: string, date: string) {
    return api.get<AttendanceRecord[]>(`/attendance/class/${classId}`, { date });
  },

  markAttendance(payload: BulkAttendancePayload) {
    return api.post<void>(`/attendance/class/${payload.class_id}`, {
      date: payload.date,
      records: payload.records,
    });
  },

  submitJustification(recordId: string, justification: string, file?: File) {
    const formData = new FormData();
    formData.append('reason', justification);
    if (file) {
      formData.append('file', file);
    }
    return api.post<void>(`/attendance/${recordId}/justify`, formData);
  },

  getAttendanceTrends(classId: string, from: string, to: string) {
    return api.get<AttendanceTrend[]>('/analytics/attendance/trends', {
      class_id: classId,
      from,
      to,
    });
  },

  getAttendanceAlerts(schoolId: string) {
    return api.get<AttendanceAlert[]>('/analytics/attendance/alerts', {
      school_id: schoolId,
    });
  },

  getStudentHistory(studentId: string) {
    return api.get<AttendanceRecord[]>(`/analytics/attendance/student/${studentId}`);
  },

  getClassStats(classId: string) {
    return api.get<AttendanceClassStats>(`/analytics/attendance/class/${classId}`);
  },

  exportAttendance(classId: string, format: 'csv' | 'pdf') {
    return api.get<AttendanceExportResponse>('/analytics/attendance/export', {
      class_id: classId,
      format,
    });
  },

  submitJustificationDirect(payload: JustificationPayload) {
    return api.post<Justification>('/attendance/justifications', payload);
  },

  reviewJustification(justificationId: string, payload: JustificationReviewPayload) {
    return api.put<Justification>(`/attendance/justifications/${justificationId}/review`, payload);
  },
};
