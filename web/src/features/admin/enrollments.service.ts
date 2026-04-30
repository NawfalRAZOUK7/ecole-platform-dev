/**
 * Admin Enrollments — typed API client (G49 Phase 2.b).
 *
 * Maps to the backend endpoint:
 *   GET /admin/enrollments  (PERM-ERP:enrollment:read for ADM/DIR)
 */

import { api } from '@/services/api/client';
import type { ProgramSummary } from './programs.service';

export interface AdminEnrollmentRow {
  id: string;
  school_id: string;
  status: string;
  created_at: string | null;
  student: {
    id: string;
    full_name: string;
    email: string;
  };
  class_: {
    id: string;
    code: string;
    name: string;
  };
  period: {
    id: string;
    label: string | null;
    date_start: string;
    date_end: string;
  };
  academic_year: {
    id: string;
    label: string | null;
  };
  program: ProgramSummary | null;
}

export interface AdminEnrollmentFilters extends Record<string, string | number | undefined> {
  class_id?: string;
  period_id?: string;
  status?: string;
  missing_program?: number; // 1 / 0 — boolean serialised for the query string
  cursor?: string;
  limit?: number;
}

export const enrollmentsService = {
  listAdminEnrollments(filters: AdminEnrollmentFilters) {
    return api.list<AdminEnrollmentRow>('/admin/enrollments', filters);
  },
};
