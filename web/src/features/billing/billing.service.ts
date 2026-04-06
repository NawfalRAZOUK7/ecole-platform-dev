import { api } from '@/services/api/client';

export interface FeeStructure {
  id: string;
  school_id: string;
  academic_year_id: string;
  name: string;
  amount: number;
  currency: string;
  frequency: string;
  due_day: number;
  applies_to_level: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface FeeStructureInput {
  academic_year_id?: string;
  name: string;
  amount: number;
  currency: string;
  frequency: string;
  due_day: number;
  applies_to_level?: string;
}

export interface FeeAssignment {
  id: string;
  fee_structure_id: string;
  student_id: string;
  school_id: string;
  discount_percent: number | null;
  discount_reason: string | null;
  status: string;
  created_at: string;
}

export interface FeeAssignmentInput {
  fee_structure_id: string;
  student_id: string;
  discount_percent?: number;
  discount_reason?: string;
}

export interface BulkFeeAssignmentInput {
  fee_structure_id: string;
  class_id?: string;
  level?: string;
  discount_percent?: number;
  discount_reason?: string;
}

export interface BulkFeeAssignmentResult {
  created: number;
  skipped: number;
}

export interface GenerateInvoicesInput {
  fee_structure_id: string;
  period_id?: string;
  issued_date: string;
  due_date: string;
}

export interface GenerateInvoicesResult {
  generated: number;
  skipped: number;
  total_amount: number;
  currency: string;
}

export interface SiblingPolicy {
  id?: string;
  discounts: Array<{ sibling_rank: number; discount_percent: number }>;
  max_siblings_covered: number;
}

export interface SiblingPolicyInput {
  discounts: Array<{ sibling_rank: number; discount_percent: number }>;
  max_siblings_covered: number;
}

export interface LateFeePolicy {
  id?: string;
  grace_period_days: number;
  fee_percent: number;
  max_fee_cap: number;
}

export interface LateFeePolicyInput {
  grace_period_days: number;
  fee_percent: number;
  max_fee_cap: number;
}

export interface PaymentPlanInstallment {
  id: string;
  plan_id: string;
  due_date: string;
  amount: number;
  status: 'pending' | 'paid' | 'overdue';
  paid_at?: string | null;
}

export interface PaymentPlan {
  id: string;
  student_id: string;
  student_name?: string;
  name: string;
  total_amount: number;
  start_date: string;
  status: 'active' | 'completed' | 'cancelled';
  installments: PaymentPlanInstallment[];
  created_at: string;
}

export interface PaymentPlanInput {
  student_id: string;
  name: string;
  total_amount: number;
  start_date: string;
  installments: Array<{ due_date: string; amount: number }>;
}

export const billingService = {
  listFeeStructures(params: Record<string, string | number | undefined> = {}) {
    return api.list<FeeStructure>('/billing/fee-structures', params);
  },

  createFeeStructure(payload: FeeStructureInput) {
    return api.post<void>('/billing/fee-structures', payload);
  },

  updateFeeStructure(feeStructureId: string, payload: FeeStructureInput) {
    return api.put<void>(`/billing/fee-structures/${feeStructureId}`, payload);
  },

  listFeeAssignments() {
    return api.list<FeeAssignment>('/billing/fee-assignments');
  },

  createFeeAssignment(payload: FeeAssignmentInput) {
    return api.post<void>('/billing/fee-assignments', payload);
  },

  createBulkFeeAssignments(payload: BulkFeeAssignmentInput) {
    return api.post<BulkFeeAssignmentResult>('/billing/fee-assignments/bulk', payload);
  },

  generateInvoices(payload: GenerateInvoicesInput) {
    return api.post<GenerateInvoicesResult>('/billing/generate-invoices', payload);
  },

  getSiblingPolicy() {
    return api.get<SiblingPolicy>('/billing/sibling-policy');
  },

  updateSiblingPolicy(payload: SiblingPolicyInput) {
    return api.put<SiblingPolicy>('/billing/sibling-policy', payload);
  },

  getLateFeePolicy() {
    return api.get<LateFeePolicy>('/billing/late-fee-policy');
  },

  updateLateFeePolicy(payload: LateFeePolicyInput) {
    return api.put<LateFeePolicy>('/billing/late-fee-policy', payload);
  },

  createPaymentPlan(payload: PaymentPlanInput) {
    return api.post<PaymentPlan>('/billing/payment-plans', payload);
  },

  listPaymentPlans(params?: Record<string, string | number | undefined>) {
    return api.list<PaymentPlan>('/billing/payment-plans', params);
  },

  getPaymentPlan(planId: string) {
    return api.get<PaymentPlan>(`/billing/payment-plans/${planId}`);
  },
};
