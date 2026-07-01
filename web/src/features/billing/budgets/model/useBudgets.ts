import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_DEFAULT } from '@/shared/hooks/useQueryDefaults';
import { budgetsService, type BudgetAllocationRequestFilters } from '../api/budgets.api';
import type {
  CreateAllocationPayload,
  CreateBudgetPayload,
  CreateBudgetRequestPayload,
  CreateTransactionPayload,
  UpdateAllocationPayload,
} from './budgets.types';

export const budgetsQueryKeys = {
  all: ['budgets'] as const,
  list: (filters: Record<string, string | number | undefined>) =>
    [...budgetsQueryKeys.all, 'list', filters] as const,
  detail: (id: string) => [...budgetsQueryKeys.all, 'detail', id] as const,
  allocations: (id: string) => [...budgetsQueryKeys.all, 'allocations', id] as const,
  allocation: (id: string) => [...budgetsQueryKeys.all, 'allocation', id] as const,
  requests: (filters: Record<string, string | number | undefined>) =>
    [...budgetsQueryKeys.all, 'requests', filters] as const,
  allocationRequests: (allocationId: string, filters: BudgetAllocationRequestFilters) =>
    [...budgetsQueryKeys.all, 'allocation-requests', allocationId, filters] as const,
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

export function useBudgetAllocation(id: string) {
  return useQuery({
    queryKey: budgetsQueryKeys.allocation(id),
    queryFn: async () => (await budgetsService.getAllocation(id)).data,
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

export function useAllocationRequests(
  allocationId: string,
  filters: BudgetAllocationRequestFilters = {},
) {
  return useQuery({
    queryKey: budgetsQueryKeys.allocationRequests(allocationId, filters),
    queryFn: async () => (await budgetsService.getAllocationRequests(allocationId, filters)).data,
    enabled: Boolean(allocationId),
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
      await Promise.all([queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all })]);
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
    mutationFn: async ({
      budgetId,
      payload,
    }: {
      budgetId: string;
      payload: CreateAllocationPayload;
    }) => budgetsService.createAllocation(budgetId, payload),
    onSuccess: async (_data, variables) => {
      await queryClient.invalidateQueries({
        queryKey: budgetsQueryKeys.allocations(variables.budgetId),
      });
    },
  });
}

export function useUpdateAllocation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      allocationId,
      payload,
    }: {
      allocationId: string;
      payload: UpdateAllocationPayload;
    }) => budgetsService.updateAllocation(allocationId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all });
    },
  });
}

export function useCreateBudgetRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateBudgetRequestPayload) =>
      budgetsService.createBudgetRequest(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all });
    },
  });
}

export function useApproveBudgetRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      requestId,
      reviewComment,
    }: {
      requestId: string;
      reviewComment?: string;
    }) => budgetsService.approveBudgetRequest(requestId, reviewComment),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all });
    },
  });
}

export function useRejectBudgetRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      requestId,
      reviewComment,
    }: {
      requestId: string;
      reviewComment?: string;
    }) => budgetsService.rejectBudgetRequest(requestId, reviewComment),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all });
    },
  });
}

export function useBudgetRequestDetail(requestId: string) {
  return useQuery({
    queryKey: [...budgetsQueryKeys.all, 'request', requestId] as const,
    queryFn: async () => (await budgetsService.getBudgetRequest(requestId)).data,
    enabled: Boolean(requestId),
    staleTime: STALE_DEFAULT,
  });
}

export function useCreateTransaction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      allocationId,
      payload,
    }: {
      allocationId: string;
      payload: CreateTransactionPayload;
    }) => (await budgetsService.createTransaction(allocationId, payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: budgetsQueryKeys.all });
    },
  });
}

export function useAllocationTransactions(allocationId: string) {
  return useQuery({
    queryKey: [...budgetsQueryKeys.all, 'allocation-transactions', allocationId] as const,
    queryFn: async () => (await budgetsService.getTransactions(allocationId)).data,
    enabled: Boolean(allocationId),
    staleTime: STALE_DEFAULT,
  });
}
