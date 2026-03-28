import { api } from '@/services/api/client';

export type ReportType =
  | 'student_report_card'
  | 'class_summary'
  | 'attendance_report'
  | 'billing_statement'
  | 'school_analytics';

export type ReportStatus = 'pending' | 'generating' | 'ready' | 'failed';

export interface ReportOption {
  id: string;
  label?: string;
  code?: string;
  name?: string;
  full_name?: string;
  email?: string;
}

export interface ReportOptionsPayload {
  classes: ReportOption[];
  periods: ReportOption[];
  students: ReportOption[];
  parents: ReportOption[];
}

export interface ReportJobItem {
  id: string;
  type: ReportType;
  status: ReportStatus;
  parameters: Record<string, string | boolean | null>;
  created_at: string;
  completed_at: string | null;
  expires_at: string | null;
  error_message: string | null;
  download_url: string | null;
  cache_hit: boolean;
}

export interface ReportHistoryFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  type?: ReportType | '';
  status?: ReportStatus | '';
}

export const reportsService = {
  getReportOptions(type: ReportType, classId?: string) {
    return api.get<ReportOptionsPayload>('/reports/options', {
      type,
      class_id: classId || undefined,
    });
  },

  listReportJobs(params: ReportHistoryFilters) {
    return api.list<ReportJobItem>('/reports', params);
  },

  generateReport(payload: Record<string, unknown>) {
    return api.post<ReportJobItem>('/reports/generate', payload);
  },
};
