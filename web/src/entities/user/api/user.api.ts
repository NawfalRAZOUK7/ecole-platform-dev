import { api } from '@/core/api/client';
import type {
  LoginHistoryEntry,
  ProfileResponse,
  AdminUserProfileResponse,
  ChildEntry,
  SessionItem,
} from '../model/types';

export interface RegisterPayload {
  code: string;
  email: string;
  full_name: string;
  phone: string | null;
  password: string;
  profile_data: Record<string, string>;
}

export interface VerifyEmailPayload {
  user_id: string;
  school_id: string;
  otp: string;
}

export interface LoginPayload {
  email: string;
  password: string;
  school_id: string;
}

export interface Verify2faPayload {
  code: string;
  user_id?: string;
}

export const userApi = {
  /** GET /auth/me */
  getMe() {
    return api.get<{
      user_id: string;
      email: string;
      full_name: string;
      role: string;
      school_id: string;
    }>('/auth/me');
  },

  /** GET /auth/login-history */
  getLoginHistory() {
    return api.get<LoginHistoryEntry[]>('/auth/login-history');
  },

  /** GET /me/profile */
  getProfile() {
    return api.get<ProfileResponse>('/me/profile');
  },

  /** GET /me/children */
  listChildren() {
    return api.get<ChildEntry[]>('/me/children');
  },

  /** GET /auth/sessions */
  listSessions() {
    return api.get<SessionItem[]>('/auth/sessions');
  },

  /** GET /admin/users/:id/profile */
  getAdminUserProfile(userId: string) {
    return api.get<AdminUserProfileResponse>(`/admin/users/${userId}/profile`);
  },
};
