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

export const authService = {
  register(payload: RegisterPayload) {
    return api.post<RegisterResponse>('/auth/register', payload);
  },

  verifyEmail(payload: VerifyEmailPayload) {
    return api.post<void>('/auth/verify-email', payload);
  },
};
