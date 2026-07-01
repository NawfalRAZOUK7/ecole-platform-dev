import { api } from '@/core/api/client';
import type {
  BudgetAllocation,
  BudgetAnalytics,
  BudgetEnvelope,
  BudgetRequest,
  BudgetRequestStatus,
  BudgetTransaction,
  CreateAllocationPayload,
  CreateBudgetPayload,
  CreateBudgetRequestPayload,
  CreateTransactionPayload,
  UpdateAllocationPayload,
} from '@/entities/billing/budget/model/types';

export interface BudgetAllocationRequestFilters extends Record<
  string,
  string | number | undefined
> {
  requester_id?: string;
  status?: BudgetRequestStatus;
}

function buildMeta() {
  return {
    timestamp: new Date().toISOString(),
    version: '0.1.0',
  };
}

export const budgetsService = {
  listBudgets(params?: Record<string, string | number | undefined>) {
    return api.list<BudgetEnvelope>('/budgets', params);
  },

  createBudget(payload: CreateBudgetPayload) {
    return api.post<BudgetEnvelope>('/budgets', payload);
  },

  getBudgetDetail(id: string) {
    return api.get<BudgetEnvelope>(`/budgets/${id}`);
  },

  updateBudget(id: string, payload: Partial<CreateBudgetPayload>) {
    return api.put<BudgetEnvelope>(`/budgets/${id}`, payload);
  },

  deleteBudget(id: string) {
    return api.delete<void>(`/budgets/${id}`);
  },

  getBudgetAllocations(id: string) {
    return api.get<BudgetAllocation[]>(`/budgets/${id}/allocations`);
  },

  createAllocation(id: string, payload: CreateAllocationPayload) {
    return api.post<BudgetAllocation>(`/budgets/${id}/allocations`, payload);
  },

  getAllocation(allocationId: string) {
    return api.get<BudgetAllocation>(`/budgets/allocations/${allocationId}`);
  },

  updateAllocation(id: string, payload: UpdateAllocationPayload) {
    return api.put<BudgetAllocation>(`/budgets/allocations/${id}`, payload);
  },

  getAllocationRequests(allocationId: string, params?: BudgetAllocationRequestFilters) {
    return api.list<BudgetRequest>(`/budgets/allocations/${allocationId}/requests`, params);
  },

  async listBudgetRequests(params?: Record<string, string | number | undefined>) {
    const requestStatus =
      params?.status === 'pending' ||
      params?.status === 'approved' ||
      params?.status === 'rejected' ||
      params?.status === 'cancelled'
        ? params.status
        : undefined;

    const budgetIds =
      params?.budget_id !== undefined
        ? [String(params.budget_id)]
        : (await budgetsService.listBudgets()).data.map((budget) => budget.id);

    const allocationPages = await Promise.all(
      budgetIds.map((budgetId) => api.list<BudgetAllocation>(`/budgets/${budgetId}/allocations`)),
    );
    const allocations = allocationPages.flatMap((page) => page.data);

    if (allocations.length === 0) {
      return {
        data: [] as BudgetRequest[],
        meta: allocationPages[0]?.meta ?? buildMeta(),
      };
    }

    const requestPages = await Promise.all(
      allocations.map((allocation) =>
        budgetsService.getAllocationRequests(allocation.id, {
          status: requestStatus,
        }),
      ),
    );

    return {
      data: requestPages.flatMap((page) => page.data),
      meta: requestPages[0]?.meta ?? allocationPages[0]?.meta ?? buildMeta(),
    };
  },

  async createBudgetRequest(payload: CreateBudgetRequestPayload) {
    const budgetId = payload.budget_id;
    if (!budgetId) {
      throw new Error('Budget request requires a budget_id');
    }

    const allocations = await api.list<BudgetAllocation>(`/budgets/${budgetId}/allocations`);
    const targetAllocation = allocations.data[0];

    if (!targetAllocation) {
      throw new Error('Budget request requires an allocation');
    }

    return api.post<BudgetRequest>(`/budgets/allocations/${targetAllocation.id}/requests`, {
      amount: payload.amount,
      currency: 'MAD',
      description: payload.description,
      justification: payload.justification,
    });
  },

  approveBudgetRequest(id: string, review_comment?: string) {
    return api.post<BudgetRequest>(`/budgets/requests/${id}/approve`, { review_comment });
  },

  rejectBudgetRequest(id: string, review_comment?: string) {
    return api.post<BudgetRequest>(`/budgets/requests/${id}/reject`, { review_comment });
  },

  async getBudgetTransactions(id: string) {
    const allocations = await api.list<BudgetAllocation>(`/budgets/${id}/allocations`);

    if (allocations.data.length === 0) {
      return {
        data: [] as BudgetTransaction[],
        meta: allocations.meta,
      };
    }

    const transactionPages = await Promise.all(
      allocations.data.map((allocation) =>
        api.list<BudgetTransaction>(`/budgets/allocations/${allocation.id}/transactions`),
      ),
    );

    return {
      data: transactionPages.flatMap((page) => page.data),
      meta: transactionPages[0]?.meta ?? allocations.meta,
    };
  },

  getBudgetAnalytics() {
    return api.get<BudgetAnalytics>('/budgets/analytics');
  },

  getBudgetRequest(requestId: string) {
    return api.get<BudgetRequest>(`/budgets/requests/${requestId}`);
  },

  createTransaction(allocationId: string, payload: CreateTransactionPayload) {
    return api.post<BudgetTransaction>(
      `/budgets/allocations/${allocationId}/transactions`,
      payload,
    );
  },

  getTransactions(allocationId: string) {
    return api.list<BudgetTransaction>(`/budgets/allocations/${allocationId}/transactions`);
  },
};
