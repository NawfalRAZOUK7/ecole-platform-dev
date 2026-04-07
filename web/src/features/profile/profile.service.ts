import { api } from '@/services/api/client';

export type ProfileFieldValue = string | number | boolean | null | undefined;

export interface StudentProfileData {
  student_number?: string | null;
  date_of_birth?: string | null;
  class_level?: string | null;
  nationality?: string | null;
  [key: string]: ProfileFieldValue;
}

export interface ParentProfileData {
  relationship_type?: string | null;
  cin_number?: string | null;
  address?: string | null;
  profession?: string | null;
  emergency_phone?: string | null;
  [key: string]: ProfileFieldValue;
}

export interface TeacherProfileData {
  employee_id?: string | null;
  subject_specialty?: string | null;
  qualification?: string | null;
  reward_points?: number | null;
  [key: string]: ProfileFieldValue;
}

export interface ProfileResponse {
  user_id?: string;
  email?: string;
  full_name?: string;
  phone?: string | null;
  role?: string;
  school_id?: string;
  student_profile?: StudentProfileData | null;
  parent_profile?: ParentProfileData | null;
  teacher_profile?: TeacherProfileData | null;
}

export interface AdminUserProfileResponse extends ProfileResponse {
  user_id: string;
  email: string;
  full_name: string;
  phone: string | null;
  role: string;
  school_id: string;
}

export interface ChildEntry {
  user_id: string;
  full_name: string;
  email: string;
  link_id: string;
  linked_at: string | null;
  student_profile: {
    class_level: string | null;
    date_of_birth: string | null;
    student_number: string | null;
    nationality: string | null;
  } | null;
}

export interface SessionItem {
  id: string;
  source: string;
  user_agent: string | null;
  ip_address: string | null;
  device_name: string | null;
  created_at: string;
  last_active: string | null;
  is_current: boolean;
}

export const profileService = {
  listSessions() {
    return api.get<SessionItem[]>('/auth/sessions');
  },

  revokeSession(sessionId: string) {
    return api.delete<void>(`/auth/sessions/${sessionId}`);
  },

  setupTwoFactor() {
    return api.post<{ provisioning_uri: string; secret: string }>('/auth/2fa/setup');
  },

  verifyTwoFactorSetup(code: string) {
    return api.post<{ backup_codes: string[]; message: string }>('/auth/2fa/verify-setup', { code });
  },

  disableTwoFactor(code: string) {
    return api.post<void>('/auth/2fa/disable', { code });
  },

  getProfile() {
    return api.get<ProfileResponse>('/me/profile');
  },

  updateProfile(payload: Record<string, string | null>) {
    return api.put<void>('/me/profile', payload);
  },

  listChildren() {
    return api.get<ChildEntry[]>('/me/children');
  },

  getAdminUserProfile(userId: string) {
    return api.get<AdminUserProfileResponse>(`/admin/users/${userId}/profile`);
  },

  changePassword(payload: { current_password: string; new_password: string }) {
    return api.post<void>('/auth/change-password', payload);
  },

  getLoginHistory() {
    return api.get<import('@/features/auth/auth.service').LoginHistoryEntry[]>('/auth/login-history');
  },
};
