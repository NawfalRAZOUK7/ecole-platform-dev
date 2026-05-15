import { api } from '@/core/api/client';
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
} from '@/entities/academic/attendance/model/types';

export interface ClassAttendanceResponse {
  class_id: string;
  stats: {
    total_students: number;
    attendance_rate: number;
    absent_count: number;
    late_count: number;
  };
  records: AttendanceRecord[];
}

export const attendanceService = {
  getClassAttendance(classId: string, date: string) {
    return api.get<ClassAttendanceResponse>(`/attendance/class/${classId}`, { date });
  },

  markAttendance(payload: BulkAttendancePayload) {
    return api.post<void>(`/attendance/class/${payload.class_id}`, {
      date: payload.date,
      records: payload.records,
    });
  },

  submitJustification(recordId: string, justification: string, file?: File) {
    const form = new FormData();
    form.append('attendance_record_id', recordId);
    form.append('reason', justification);
    if (file) {
      form.append('attachment', file);
    }
    return api.post<Justification>('/attendance/justifications', form);
  },

  getAttendanceTrends(classId: string, from: string, to: string) {
    return api.get<AttendanceTrend[]>(`/analytics/attendance/trends/${classId}`, {
      from,
      to,
    });
  },

  getAttendanceAlerts(schoolId: string, programId?: string) {
    return api.get<AttendanceAlert[]>('/analytics/attendance/alerts', {
      school_id: schoolId,
      program_id: programId || undefined,
    });
  },

  getStudentHistory(studentId: string) {
    return api.get<AttendanceRecord[]>(`/analytics/attendance/student/${studentId}`);
  },

  getClassStats(classId: string) {
    return api.get<AttendanceClassStats>(`/analytics/attendance/class/${classId}`);
  },

  async exportAttendance(classId: string, format: 'csv' | 'pdf') {
    const endpoint = format === 'pdf' ? '/api/v1/export/xlsx' : '/api/v1/export/csv';
    const filters = JSON.stringify({ class_id: classId, scope: 'attendance' });
    const response = await fetch(
      `${endpoint}?entity=attendance&filters=${encodeURIComponent(filters)}`,
      {
        headers: {
          Accept: format === 'pdf' ? 'application/octet-stream' : 'text/csv',
        },
        credentials: 'include',
      },
    );

    if (!response.ok) {
      throw new Error('Attendance export failed');
    }

    const blob = await response.blob();
    const filename = `attendance-${classId}.${format === 'pdf' ? 'xlsx' : 'csv'}`;
    const downloadUrl = URL.createObjectURL(blob);

    return {
      data: {
        download_url: downloadUrl,
        file_name: filename,
      } satisfies AttendanceExportResponse,
      meta: {
        timestamp: new Date().toISOString(),
        version: '0.1.0',
      },
    };
  },

  exportAttendanceAnalytics(classId: string) {
    return api.get<AttendanceClassStats>(`/analytics/attendance/class/${classId}`, {
      export: 'true',
    });
  },

  submitJustificationDirect(payload: JustificationPayload) {
    const form = new FormData();
    form.append('student_id', payload.student_id);
    form.append('class_id', payload.class_id);
    form.append('date', payload.date);
    form.append('reason', payload.reason);
    return api.post<Justification>('/attendance/justifications', form);
  },

  reviewJustification(justificationId: string, payload: JustificationReviewPayload) {
    return api.post<Justification>(`/attendance/justifications/${justificationId}/review`, payload);
  },

  checkThresholds() {
    return api.post<
      {
        class_id: string;
        student_id: string;
        attendance_rate: number;
        threshold: number;
        triggered: boolean;
      }[]
    >('/analytics/attendance/check-thresholds', {});
  },
};
