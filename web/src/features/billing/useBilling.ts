import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_INVOICES } from '@/shared/hooks/useQueryDefaults';
import {
  billingService,
  type BulkFeeAssignmentInput,
  type FeeAssignmentInput,
  type FeeStructureInput,
  type GenerateInvoicesInput,
} from './billing.service';

export const billingQueryKeys = {
  all: ['billing'] as const,
  feeStructures: (status?: string) => [...billingQueryKeys.all, 'fee-structures', status || 'all'] as const,
  feeAssignments: () => [...billingQueryKeys.all, 'fee-assignments'] as const,
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
