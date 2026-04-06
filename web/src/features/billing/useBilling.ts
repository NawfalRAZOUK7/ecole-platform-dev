import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_INVOICES } from '@/shared/hooks/useQueryDefaults';
import {
  billingService,
  type BulkFeeAssignmentInput,
  type FeeAssignmentInput,
  type FeeStructureInput,
  type GenerateInvoicesInput,
  type LateFeePolicyInput,
  type PaymentPlanInput,
  type SiblingPolicyInput,
} from './billing.service';

export const billingQueryKeys = {
  all: ['billing'] as const,
  feeStructures: (status?: string) => [...billingQueryKeys.all, 'fee-structures', status || 'all'] as const,
  feeAssignments: () => [...billingQueryKeys.all, 'fee-assignments'] as const,
  siblingPolicy: () => [...billingQueryKeys.all, 'sibling-policy'] as const,
  lateFeePolicy: () => [...billingQueryKeys.all, 'late-fee-policy'] as const,
  paymentPlans: (params?: Record<string, string | number | undefined>) =>
    [...billingQueryKeys.all, 'payment-plans', params ?? {}] as const,
  paymentPlan: (planId: string) => [...billingQueryKeys.all, 'payment-plan', planId] as const,
};

export function useFeeStructures(status?: string) {
  return useQuery({
    queryKey: billingQueryKeys.feeStructures(status),
    queryFn: async () => (await billingService.listFeeStructures(status ? { status } : {})).data,
    staleTime: STALE_INVOICES,
  });
}

export function useFeeAssignments() {
  return useQuery({
    queryKey: billingQueryKeys.feeAssignments(),
    queryFn: async () => (await billingService.listFeeAssignments()).data,
    staleTime: STALE_INVOICES,
  });
}

export function useCreateFeeStructure() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: FeeStructureInput) => {
      await billingService.createFeeStructure(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: [...billingQueryKeys.all, 'fee-structures'] });
    },
  });
}

export function useUpdateFeeStructure() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      feeStructureId,
      payload,
    }: {
      feeStructureId: string;
      payload: FeeStructureInput;
    }) => {
      await billingService.updateFeeStructure(feeStructureId, payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: [...billingQueryKeys.all, 'fee-structures'] });
    },
  });
}

export function useCreateFeeAssignment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: FeeAssignmentInput) => {
      await billingService.createFeeAssignment(payload);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: billingQueryKeys.feeAssignments() });
    },
  });
}

export function useBulkFeeAssignments() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: BulkFeeAssignmentInput) =>
      (await billingService.createBulkFeeAssignments(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: billingQueryKeys.feeAssignments() });
    },
  });
}

export function useGenerateInvoices() {
  return useMutation({
    mutationFn: async (payload: GenerateInvoicesInput) =>
      (await billingService.generateInvoices(payload)).data,
  });
}

export function useSiblingPolicy() {
  return useQuery({
    queryKey: billingQueryKeys.siblingPolicy(),
    queryFn: async () => (await billingService.getSiblingPolicy()).data,
    staleTime: STALE_INVOICES,
  });
}

export function useUpdateSiblingPolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: SiblingPolicyInput) =>
      (await billingService.updateSiblingPolicy(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: billingQueryKeys.siblingPolicy() });
    },
  });
}

export function useLateFeePolicy() {
  return useQuery({
    queryKey: billingQueryKeys.lateFeePolicy(),
    queryFn: async () => (await billingService.getLateFeePolicy()).data,
    staleTime: STALE_INVOICES,
  });
}

export function useUpdateLateFeePolicy() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LateFeePolicyInput) =>
      (await billingService.updateLateFeePolicy(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: billingQueryKeys.lateFeePolicy() });
    },
  });
}

export function usePaymentPlans(params?: Record<string, string | number | undefined>) {
  return useQuery({
    queryKey: billingQueryKeys.paymentPlans(params),
    queryFn: async () => (await billingService.listPaymentPlans(params)).data,
    staleTime: STALE_INVOICES,
  });
}

export function useCreatePaymentPlan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: PaymentPlanInput) =>
      (await billingService.createPaymentPlan(payload)).data,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: [...billingQueryKeys.all, 'payment-plans'] });
    },
  });
}

export function usePaymentPlan(planId: string) {
  return useQuery({
    queryKey: billingQueryKeys.paymentPlan(planId),
    queryFn: async () => (await billingService.getPaymentPlan(planId)).data,
    enabled: Boolean(planId),
    staleTime: STALE_INVOICES,
  });
}
