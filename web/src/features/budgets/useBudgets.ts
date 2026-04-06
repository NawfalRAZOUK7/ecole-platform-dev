import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { budgetsService } from './budgets.service';
import type { CreateAllocationPayload, CreateBudgetPayload, CreateBudgetRequestPayload } from './budgets.types';

export const budgetsQueryKeys = {
  all: ['budgets'] as const,
  list: (filters: Record<string, string | number | undefined>) =>
    [...budgetsQueryKeys.all, 'list', filters] as const,
  detail: (id: string) => [...budgetsQueryKeys.all, 'detail', id] as const,
  allocations: (id: string) => [...budgetsQueryKeys.all, 'allocations', id] as const,
  requests: (filters: Record<string, string | number | undefined>) =>
    [...budgetsQueryKeys.all, 'requests', filters] as const,
  transactions: (id: string) => [...budgetsQueryKeys.all, 'transactions', id] as const,
  analytics: () => [...budgetsQueryKeys.all, 'analytics'] as const,
};

export function useBudgets(filters: Record<string, string | number | undefined> = {}) {
  return useQuery({
    queryKey: budgetsQueryKeys.list(filters),
    queryFn: async () => (await budgetsService.listBudgets(filters)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useBudgetDetail(id: string) {
  return useQuery({
    queryKey: budgetsQueryKeys.detail(id),
    queryFn: async () => (await budgetsService.getBudgetDetail(id)).data,
    enabled: Boolean(id),
    staleTime: STALE_DEFAULT,
  });
}

export function useBudgetAllocations(id: string) {
  return useQuery({
    queryKey: budgetsQueryKeys.allocations(id),
    queryFn: async () => (await budgetsService.getBudgetAllocations(id)).data,
    enabled: Boolean(id),
    staleTime: STALE_DEFAULT,
  });
}

export function useBudgetRequests(filters: Record<string, string | number | undefined> = {}) {
  return useQuery({
    queryKey: budgetsQueryKeys.requests(filters),
    queryFn: async () => (await budgetsService.listBudgetRequests(filters)).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useBudgetTransactions(id: string) {
  return useQuery({
    queryKey: budgetsQueryKeys.transactions(id),
    queryFn: async () => (await budgetsService.getBudgetTransactions(id)).data,
    enabled: Boolean(id),
    staleTime: STALE_DEFAULT,
  });
}

export function useBudgetAnalytics() {
  return useQuery({
    queryKey: budgetsQueryKeys.analytics(),
    queryFn: async () => (await budgetsService.getBudgetAnalytics()).data,
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateBudgetPayload) => budgetsService.createBudget(payload),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all }),
      ]);
    },
  });
}

export function useDeleteBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (budgetId: string) => budgetsService.deleteBudget(budgetId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all });
    },
  });
}

export function useCreateAllocation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ budgetId, payload }: { budgetId: string; payload: CreateAllocationPayload }) =>
      budgetsService.createAllocation(budgetId, payload),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.allocations(variables.budgetId) });
    },
  });
}

export function useUpdateAllocation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ allocationId, payload }: { allocationId: string; payload: Partial<CreateAllocationPayload> }) =>
      budgetsService.updateAllocation(allocationId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all });
    },
  });
}

export function useCreateBudgetRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateBudgetRequestPayload) => budgetsService.createBudgetRequest(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all });
    },
  });
}

export function useApproveBudgetRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ requestId, reviewComment }: { requestId: string; reviewComment?: string }) =>
      budgetsService.approveBudgetRequest(requestId, reviewComment),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all });
    },
  });
}

export function useRejectBudgetRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ requestId, reviewComment }: { requestId: string; reviewComment?: string }) =>
      budgetsService.rejectBudgetRequest(requestId, reviewComment),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all });
    },
  });
}
