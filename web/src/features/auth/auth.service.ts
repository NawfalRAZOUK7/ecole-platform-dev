import { api } from '@/services/api/client';

export interface RegisterPayload {
  code: string;
  email: string;
  full_name: string;
  phone: string | null;
  password: string;
  profile_data: Record<string, string>;
}

export interface RegisterResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  school_id: string;
  role: string;
  email_verification_required: boolean;
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

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  school_id: string;
  role: string;
  requires_2fa?: boolean;
}

export interface LoginHistoryEntry {
  id: string;
  ip_address: string | null;
  user_agent: string | null;
  location: string | null;
  status: 'success' | 'failed';
  created_at: string;
}

export const authService = {
  register(payload: RegisterPayload) {
    return api.post<RegisterResponse>('/auth/register', payload);
  },

  verifyEmail(payload: VerifyEmailPayload) {
    return api.post<void>('/auth/verify-email', payload);
  },

  login(payload: LoginPayload) {
    return api.post<LoginResponse>('/auth/login', payload);
  },

  refresh() {
    return api.post<{ access_token: string; expires_in: number }>('/auth/refresh', {});
  },

  logout() {
    return api.post<void>('/auth/logout', {});
  },

  getMe() {
    return api.get<{ user_id: string; email: string; full_name: string; role: string; school_id: string }>('/auth/me');
  },

  getLoginHistory() {
    return api.get<LoginHistoryEntry[]>('/auth/login-history');
  },

  requestRecovery(email: string) {
    return api.post<void>('/recovery/request', { email });
  },

  verifyRecovery(token: string, code: string) {
    return api.post<{ valid: boolean }>('/recovery/verify', { token, code });
  },

  resetPassword(token: string, new_password: string) {
    return api.post<void>('/recovery/reset', { token, new_password });
  },
};
