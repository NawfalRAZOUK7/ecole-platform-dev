import { api } from '@/services/api/client';
import type {
  BudgetAllocation,
  BudgetAnalytics,
  BudgetEnvelope,
  BudgetRequest,
  BudgetTransaction,
  CreateAllocationPayload,
  CreateBudgetPayload,
  CreateBudgetRequestPayload,
  UpdateAllocationPayload,
} from './budgets.types';

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

  updateAllocation(id: string, payload: UpdateAllocationPayload) {
    return api.put<BudgetAllocation>(`/budgets/allocations/${id}`, payload);
  },

  listBudgetRequests(params?: Record<string, string | number | undefined>) {
    return api.get<BudgetRequest[]>('/budgets/requests', params);
  },

  createBudgetRequest(payload: CreateBudgetRequestPayload) {
    return api.post<BudgetRequest>('/budgets/requests', payload);
  },

  approveBudgetRequest(id: string, review_comment?: string) {
    return api.put<BudgetRequest>(`/budgets/requests/${id}/approve`, { review_comment });
  },

  rejectBudgetRequest(id: string, review_comment?: string) {
    return api.put<BudgetRequest>(`/budgets/requests/${id}/reject`, { review_comment });
  },

  getBudgetTransactions(id: string) {
    return api.get<BudgetTransaction[]>(`/budgets/${id}/transactions`);
  },

  getBudgetAnalytics() {
    return api.get<BudgetAnalytics>('/budgets/analytics');
  },
};
