import { useEffect, useState } from 'react';
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT, STALE_NOTIFICATIONS } from '@/shared/hooks/useQueryDefaults';
import {
  adminService,
  type AdminAuditFilters,
  type AdminInvitationFilters,
  type AdminJustificationFilters,
  type AdminParentChildLinkFilters,
  type AdminUsersFilters,
  type CsvRow,
  type KpiItem,
  type ParentChildLink,
  type ParentChildLinkRow,
} from './admin.service';

const AUTO_REFRESH_MS = 5 * 60 * 1000;

export const adminQueryKeys = {
  all: ['admin'] as const,
  dashboard: () => [...adminQueryKeys.all, 'dashboard'] as const,
  analytics: (period: number) => [...adminQueryKeys.all, 'analytics', period] as const,
  auditLogs: (filters: AdminAuditFilters) => [...adminQueryKeys.all, 'audit', filters] as const,
  users: (filters: AdminUsersFilters) => [...adminQueryKeys.all, 'users', filters] as const,
  userSearch: (search: string, role: string) => [...adminQueryKeys.all, 'user-search', role, search] as const,
  invitations: (filters: AdminInvitationFilters) => [...adminQueryKeys.all, 'invitations', filters] as const,
  justifications: (filters: AdminJustificationFilters) => [...adminQueryKeys.all, 'justifications', filters] as const,
  parentChildLinks: (filters: AdminParentChildLinkFilters) => [...adminQueryKeys.all, 'parent-child-links', filters] as const,
};

async function enrichParentChildLinks(items: ParentChildLink[]): Promise<ParentChildLinkRow[]> {
  const ids = Array.from(new Set(items.flatMap((item) => [item.parent_user_id, item.child_user_id])));
  const profiles = await Promise.all(
    ids.map(async (id) => {
      try {
        const profile = (await adminService.getUserProfile(id)).data;
        return [id, profile.full_name || profile.email] as const;
      } catch {
        return [id, `${id.slice(0, 8)}...`] as const;
      }
    })
  );
  const nameMap = Object.fromEntries(profiles);

  return items.map((item) => ({
    ...item,
    parent_name: nameMap[item.parent_user_id] || `${item.parent_user_id.slice(0, 8)}...`,
    child_name: nameMap[item.child_user_id] || `${item.child_user_id.slice(0, 8)}...`,
  }));
}

export function useAdminDashboard() {
  return useQuery({
    queryKey: adminQueryKeys.dashboard(),
    queryFn: async () => (await adminService.getDashboard()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useAdminAnalytics(period: number) {
  const query = useQuery({
    queryKey: adminQueryKeys.analytics(period),
    queryFn: async () => (await adminService.getKpis(period)).data,
    staleTime: STALE_DEFAULT,
    refetchInterval: AUTO_REFRESH_MS,
  });
  const [history, setHistory] = useState<KpiItem[][]>([]);

  useEffect(() => {
    setHistory([]);
  }, [period]);

  useEffect(() => {
    if (!query.data?.kpis?.length) {
      return;
    }
    setHistory((current) => {
      const next = [...current, query.data.kpis];
      return next.length > 10 ? next.slice(-10) : next;
    });
  }, [query.data?.computed_at, query.data?.kpis]);

  return {
    ...query,
    history,
  };
}

export function useAdminAuditLogs(filters: AdminAuditFilters) {
  return useInfiniteQuery({
    queryKey: adminQueryKeys.auditLogs(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      adminService.listAuditLogs({
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useAdminUsers(filters: AdminUsersFilters) {
  return useInfiniteQuery({
    queryKey: adminQueryKeys.users(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      adminService.listUsers({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useAdminUserSearch(search: string, role: string) {
  return useQuery({
    queryKey: adminQueryKeys.userSearch(search, role),
    queryFn: async () => (await adminService.listUsers({ search, role, limit: 10 })).data,
    enabled: search.trim().length >= 2,
    staleTime: STALE_DEFAULT,
  });
}

export function useSuspendAdminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userId: string) => {
      await adminService.suspendUser(userId);
      return userId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useActivateAdminUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userId: string) => {
      await adminService.activateUser(userId);
      return userId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useChangeAdminUserRole() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: string }) => {
      await adminService.changeUserRole(userId, role);
      return { userId, role };
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });
}

export function useAdminBatchRegister() {
  return useMutation({
    mutationFn: async (rows: CsvRow[]) => (await adminService.registerBatch(rows)).data,
  });
}

export function useAdminInvitations(filters: AdminInvitationFilters) {
  return useInfiniteQuery({
    queryKey: adminQueryKeys.invitations(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      adminService.listInvitations({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_NOTIFICATIONS,
  });
}

export function useCreateInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: Parameters<typeof adminService.createInvitation>[0]) =>
      (await adminService.createInvitation(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'invitations'] });
    },
  });
}

export function useRevokeInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (inviteId: string) => {
      await adminService.revokeInvitation(inviteId);
      return inviteId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'invitations'] });
    },
  });
}

export function useAdminJustifications(filters: AdminJustificationFilters) {
  return useInfiniteQuery({
    queryKey: adminQueryKeys.justifications(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      adminService.listJustifications({
        limit: 20,
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useReviewJustification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      justificationId,
      decision,
      rejectionReason,
    }: {
      justificationId: string;
      decision: 'justified' | 'rejected';
      rejectionReason?: string;
    }) => {
      await adminService.reviewJustification(justificationId, {
        decision,
        rejection_reason: rejectionReason,
      });
      return { justificationId, decision, rejectionReason };
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'justifications'] });
    },
  });
}

export function useAdminParentChildLinks(filters: AdminParentChildLinkFilters) {
  return useInfiniteQuery({
    queryKey: adminQueryKeys.parentChildLinks(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ pageParam }) => {
      const response = await adminService.listParentChildLinks({
        limit: 20,
        ...filters,
        cursor: pageParam,
      });
      return {
        ...response,
        data: await enrichParentChildLinks(response.data),
      };
    },
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateParentChildLink() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      parentUserId,
      childUserId,
    }: {
      parentUserId: string;
      childUserId: string;
    }) => {
      await adminService.createParentChildLink(parentUserId, childUserId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'parent-child-links'] });
    },
  });
}

export function useRevokeParentChildLink() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (linkId: string) => {
      await adminService.revokeParentChildLink(linkId);
      return linkId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['admin', 'parent-child-links'] });
    },
  });
}
