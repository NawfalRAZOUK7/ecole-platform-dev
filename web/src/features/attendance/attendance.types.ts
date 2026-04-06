export type AttendanceStatus = 'present' | 'absent' | 'late' | 'excused';

export interface AttendanceRecord {
  id: string;
  student_id: string;
  student_name: string;
  class_id: string;
  date: string;
  status: AttendanceStatus;
  justified: boolean;
  justification?: string;
  marked_by: string;
}

export interface BulkAttendancePayload {
  class_id: string;
  date: string;
  records: Array<{
    student_id: string;
    status: AttendanceStatus;
    note?: string;
  }>;
}

export interface AttendanceTrend {
  date: string;
  present: number;
  absent: number;
  late: number;
  total: number;
}

export interface AttendanceAlert {
  student_id: string;
  student_name: string;
  absent_count: number;
  consecutive_absences: number;
  alert_level: 'warning' | 'critical';
}

export interface AttendanceClassStats {
  total_students: number;
  attendance_rate: number;
  absent_count: number;
  late_count: number;
}

export interface AttendanceExportResponse {
  download_url?: string;
  file_name?: string;
  content?: string;
}

export interface JustificationMutationInput {
  recordId: string;
  justification: string;
  file?: File;
}
