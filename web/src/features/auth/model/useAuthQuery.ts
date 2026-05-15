import { useMutation } from '@tanstack/react-query';
import {
  authService,
  type RegisterPayload,
  type RegisterResponse,
  type VerifyEmailPayload,
} from '../api/auth.api';

export function useRegister() {
  return useMutation({
    mutationFn: async (payload: RegisterPayload): Promise<RegisterResponse> =>
      (await authService.register(payload)).data,
  });
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: async (payload: VerifyEmailPayload) => {
      await authService.verifyEmail(payload);
    },
  });
}

export function useConsumeInvite() {
  return useMutation({
    mutationFn: async (code: string) => {
      await authService.consumeInvite(code);
    },
  });
}
