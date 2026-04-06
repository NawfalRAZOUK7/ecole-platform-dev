export type BudgetStatus = 'active' | 'frozen' | 'closed';
export type BudgetRequestStatus = 'pending' | 'approved' | 'rejected' | 'cancelled';
export type BudgetTransactionType = 'allocation' | 'expense' | 'refund' | 'adjustment';

export interface BudgetEnvelope {
  id: string;
  name: string;
  total_amount: number;
  spent_amount: number;
  remaining_amount: number;
  status: BudgetStatus;
  currency: 'MAD';
  start_date: string;
  end_date: string;
  created_at: string;
}

export interface BudgetAllocation {
  id: string;
  budget_id: string;
  category: string;
  label: string;
  amount: number;
  spent: number;
  remaining: number;
  status: string;
}

export interface BudgetRequest {
  id: string;
  budget_id: string;
  allocation_id?: string;
  requester_name?: string;
  amount: number;
  category: string;
  description: string;
  justification: string;
  status: BudgetRequestStatus;
  review_comment?: string | null;
  created_at: string;
}

export interface BudgetTransaction {
  id: string;
  budget_id: string;
  allocation_id?: string;
  amount: number;
  type: BudgetTransactionType;
  description: string;
  date: string;
}

export interface BudgetAnalytics {
  total_budget: number;
  total_spent: number;
  remaining: number;
  request_count: number;
  spending_trend: Array<{ date: string; amount: number }>;
  category_breakdown: Array<{ category: string; amount: number }>;
}

export interface CreateBudgetPayload {
  name: string;
  total_amount: number;
  start_date: string;
  end_date: string;
  status?: BudgetStatus;
}

export interface CreateAllocationPayload {
  category: string;
  label: string;
  amount: number;
  status?: string;
}

export type UpdateAllocationPayload = Partial<CreateAllocationPayload>;

export interface CreateBudgetRequestPayload {
  budget_id?: string;
  category: string;
  amount: number;
  justification: string;
  description: string;
}
