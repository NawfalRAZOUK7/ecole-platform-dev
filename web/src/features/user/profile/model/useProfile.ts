import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { profileService } from '../api/profile.api';

export const profileQueryKeys = {
  all: ['profile'] as const,
  details: () => [...profileQueryKeys.all, 'details'] as const,
  adminView: (userId: string | null) => [...profileQueryKeys.all, 'admin-view', userId] as const,
  children: () => [...profileQueryKeys.all, 'children'] as const,
  sessions: () => [...profileQueryKeys.all, 'sessions'] as const,
  loginHistory: () => [...profileQueryKeys.all, 'loginHistory'] as const,
};

export function useProfileData() {
  return useQuery({
    queryKey: profileQueryKeys.details(),
    queryFn: async () => (await profileService.getProfile()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useSaveProfileData() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: Record<string, string | null>) => {
      await profileService.updateProfile(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: profileQueryKeys.details() });
    },
  });
}

export function useProfileChildren(enabled: boolean) {
  return useQuery({
    queryKey: profileQueryKeys.children(),
    queryFn: async () => (await profileService.listChildren()).data,
    enabled,
    staleTime: STALE_DEFAULT,
  });
}

export function useAdminUserProfile(userId: string | null | undefined, enabled: boolean) {
  return useQuery({
    queryKey: profileQueryKeys.adminView(userId || null),
    queryFn: async () => (await profileService.getAdminUserProfile(userId!)).data,
    enabled: enabled && Boolean(userId),
    staleTime: STALE_DEFAULT,
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (payload: { current_password: string; new_password: string }) => {
      await profileService.changePassword(payload);
    },
  });
}

export function useSessions() {
  return useQuery({
    queryKey: profileQueryKeys.sessions(),
    queryFn: async () => (await profileService.listSessions()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (sessionId: string) => {
      await profileService.revokeSession(sessionId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: profileQueryKeys.sessions() });
    },
  });
}

export function useTwoFactorSetup() {
  return useMutation({
    mutationFn: async () => (await profileService.setupTwoFactor()).data,
  });
}

export function useVerifyTwoFactorSetup() {
  return useMutation({
    mutationFn: async (code: string) => (await profileService.verifyTwoFactorSetup(code)).data,
  });
}

export function useDisableTwoFactor() {
  return useMutation({
    mutationFn: async (code: string) => {
      await profileService.disableTwoFactor(code);
    },
  });
}

export function useLoginHistory() {
  return useQuery({
    queryKey: profileQueryKeys.loginHistory(),
    queryFn: async () => (await profileService.getLoginHistory()).data,
    staleTime: STALE_DEFAULT,
  });
}
