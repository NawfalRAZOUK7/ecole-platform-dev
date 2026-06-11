import { api } from '@/core/api/client';

export type ApplicationType = 'formal_school' | 'micro_school';
export type ApplicationStatus = 'pending' | 'needs_info' | 'approved' | 'rejected';

export interface FormalSchoolApplicationPayload {
  applicant_name: string;
  applicant_email: string;
  applicant_phone?: string;
  city?: string;
  language?: string;
  org_name: string;
  address?: string;
  level_band?: string;
  subjects?: string[];
  notes?: string;
}

export interface MicroSchoolApplicationPayload {
  applicant_name: string;
  applicant_email: string;
  applicant_phone?: string;
  city?: string;
  language?: string;
  org_name: string;
  neighborhood?: string;
  address?: string;
  max_capacity?: number;
  notes?: string;
}

export interface ApplicationItem {
  id: string;
  application_type: ApplicationType;
  status: ApplicationStatus;
  applicant_name: string;
  applicant_email: string;
  applicant_phone?: string | null;
  city?: string | null;
  org_name: string;
  address?: string | null;
  neighborhood?: string | null;
  max_capacity?: number | null;
  level_band?: string | null;
  notes?: string | null;
  review_notes?: string | null;
  created_school_id?: string | null;
  created_at?: string | null;
}

export interface ApproveResult {
  application_id: string;
  status: string;
  created_school_id: string;
  created_user_id: string;
  role_target: string;
  /** One-click set-password link emailed to the owner. */
  activation_url: string;
  /** Plaintext token — only present outside production (dev convenience). */
  activation_token?: string;
}

export interface ResendActivationResult {
  application_id: string;
  status: string;
  created_user_id: string;
  role_target: string;
  activation_url: string;
  activation_token?: string;
}

export interface ActivateResult {
  user_id: string;
  email: string;
  status: string;
  activated: boolean;
}

export const applicationsService = {
  submitFormalSchool(payload: FormalSchoolApplicationPayload) {
    return api.post<ApplicationItem>('/applications/formal-school', payload);
  },
  submitMicroSchool(payload: MicroSchoolApplicationPayload) {
    return api.post<ApplicationItem>('/applications/micro-school', payload);
  },
  list(params: { status?: string; type?: string } = {}) {
    return api.list<ApplicationItem>('/platform/applications', params);
  },
  uploadAttachment(applicationId: string, file: File, kind = 'other') {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('kind', kind);
    return api.post<{ id: string; file_path: string }>(
      `/applications/${applicationId}/attachments`,
      fd,
    );
  },
  get(id: string) {
    return api.get<ApplicationItem>(`/platform/applications/${id}`);
  },
  approve(id: string) {
    return api.post<ApproveResult>(`/platform/applications/${id}/approve`);
  },
  resendActivation(id: string) {
    return api.post<ResendActivationResult>(
      `/platform/applications/${id}/resend-activation`,
    );
  },
  reject(id: string, review_notes?: string) {
    return api.post<ApplicationItem>(`/platform/applications/${id}/reject`, { review_notes });
  },
  requestInfo(id: string, review_notes?: string) {
    return api.post<ApplicationItem>(`/platform/applications/${id}/request-info`, {
      review_notes,
    });
  },
  activate(token: string, password: string) {
    return api.post<ActivateResult>('/auth/activate', { token, password });
  },
};
