import { api } from '@/core/api/client';
import type { SchoolRecord } from '@/features/school/settings/api/schools.api';

export interface AdminCursorFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  limit?: number;
}

export interface DashboardData {
  users: number;
  active_sessions: number;
  active_invitations: number;
  audit_events_24h: number;
  pending_justifications: number;
  users_by_role: Record<string, number>;
}

export interface UserItem {
  id: string;
  email: string;
  full_name: string;
  status: string;
  role: string;
  created_at: string | null;
  email_verified: boolean;
  totp_enabled: boolean;
}

export interface AuditEntry {
  id: string;
  action_type: string;
  outcome: string;
  actor_id: string | null;
  target_type: string | null;
  target_id: string | null;
  error_code: string | null;
  correlation_id: string | null;
  ip_address: string | null;
  created_at: string | null;
}

export interface CsvRow {
  email: string;
  full_name: string;
  role: string;
  phone?: string;
  class_code?: string;
}

export interface BatchResult {
  created: Array<{
    user_id: string;
    email: string;
    full_name: string;
    role: string;
    temp_password: string;
  }>;
  errors: Array<{ email: string; error: string }>;
  total_created: number;
  total_errors: number;
}

export interface Invitation {
  id: string;
  role_target: string;
  consumed_at: string | null;
  consumed_by: string | null;
  expires_at: string;
  created_at: string | null;
  issuer_user_id: string | null;
  status: string;
}

export interface Justification {
  id: string;
  attendance_record_id: string;
  parent_id: string;
  status: string;
  reason: string | null;
  rejection_reason: string | null;
  created_at: string | null;
}

export interface ParentChildLink {
  id: string;
  parent_user_id: string;
  child_user_id: string;
  school_id: string;
  status: string;
  linked_at: string | null;
  linked_by: string | null;
}

export interface ParentChildLinkRow extends ParentChildLink {
  parent_name: string;
  child_name: string;
}

export interface UserEntry {
  id: string;
  full_name: string;
  email: string;
  role: string;
}

export interface UserProfileSummary {
  email: string;
  full_name: string;
  role: string;
}

export interface KpiItem {
  kpi_id: string;
  name: string;
  value: number | null;
  unit: string;
  numerator?: number;
  denominator?: number;
  period: string;
  threshold?: string;
  data_source?: string;
  note?: string;
  computed_at?: string;
}

export interface KpisResponse {
  kpis: KpiItem[];
  period: string;
  computed_at: string;
}

export interface AdminUsersFilters extends AdminCursorFilters {
  search?: string;
  role?: string;
  status?: string;
}

export interface AdminAuditFilters extends AdminCursorFilters {
  correlation_id?: string;
  action_type?: string;
  date_from?: string;
  date_to?: string;
}

export interface AdminInvitationFilters extends AdminCursorFilters {
  status?: string;
}

export interface AdminJustificationFilters extends AdminCursorFilters {
  status?: string;
}

export interface AdminParentChildLinkFilters extends AdminCursorFilters {
  status?: string;
  parent_id?: string;
  student_id?: string;
}

export interface InvitationCreatePayload {
  role_target: string;
  expires_in_hours: number;
  target_student_id?: string;
}

export interface AdminLoginHistoryEntry {
  id: string;
  ip_address: string | null;
  user_agent: string | null;
  location: string | null;
  status: 'success' | 'failed';
  created_at: string;
}

export interface CreateSchoolPayload {
  name: string;
  code: string;
  address?: string;
  city?: string;
  phone?: string;
  email?: string;
  timezone?: string;
  default_language?: string;
}

export const adminService = {
  getDashboard() {
    return api.get<DashboardData>('/admin/dashboard');
  },

  getKpis(period: number) {
    return api.get<KpisResponse>('/kpis', { period });
  },

  listAuditLogs(params: AdminAuditFilters) {
    return api.list<AuditEntry>('/admin/audit-logs', params);
  },

  listUsers(params: AdminUsersFilters) {
    return api.list<UserItem>('/admin/users', params);
  },

  suspendUser(userId: string) {
    return api.put<void>(`/admin/users/${userId}/suspend`);
  },

  activateUser(userId: string) {
    return api.put<void>(`/admin/users/${userId}/activate`);
  },

  changeUserRole(userId: string, role: string) {
    return api.put<void>(`/admin/users/${userId}/role?role=${encodeURIComponent(role)}`);
  },

  registerBatch(users: CsvRow[]) {
    return api.post<BatchResult>('/admin/register-batch', { users });
  },

  listInvitations(params: AdminInvitationFilters) {
    return api.list<Invitation>('/admin/invitations', params);
  },

  createInvitation(body: InvitationCreatePayload) {
    return api.post<{ code: string }>('/invites/create', body);
  },

  revokeInvitation(inviteId: string) {
    return api.post<void>('/invites/revoke', { invite_id: inviteId });
  },

  listJustifications(params: AdminJustificationFilters) {
    return api.list<Justification>('/admin/justifications', params);
  },

  reviewJustification(
    justificationId: string,
    body: { decision: 'justified' | 'rejected'; rejection_reason?: string },
  ) {
    return api.post<void>(`/attendance/justifications/${justificationId}/review`, body);
  },

  listParentChildLinks(params: AdminParentChildLinkFilters) {
    return api.list<ParentChildLink>('/admin/parent-child-links', params);
  },

  getUserProfile(userId: string) {
    return api.get<UserProfileSummary>(`/admin/users/${userId}/profile`);
  },

  createParentChildLink(parentUserId: string, childUserId: string) {
    return api.post<void>(
      `/admin/parent-child-links?parent_user_id=${encodeURIComponent(parentUserId)}&child_user_id=${encodeURIComponent(childUserId)}`,
    );
  },

  revokeParentChildLink(linkId: string) {
    return api.delete<void>(`/admin/parent-child-links/${linkId}`);
  },

  impersonateUser(userId: string) {
    return api.post<{ access_token: string; user_id: string; role: string }>(
      `/admin/impersonate/${userId}`,
      {},
    );
  },

  stopImpersonation() {
    return api.post<void>('/admin/stop-impersonation', {});
  },

  getUserLoginHistory(userId: string) {
    return api.get<AdminLoginHistoryEntry[]>(`/admin/users/${userId}/login-history`);
  },

  createSchool(payload: CreateSchoolPayload) {
    return api.post<SchoolRecord>('/schools', payload);
  },

  listSchools() {
    return api.list<SchoolRecord>('/schools');
  },
};
