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
};
