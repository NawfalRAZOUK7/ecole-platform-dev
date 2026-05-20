import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { STALE_INVOICES } from '@/shared/hooks/useQueryDefaults';
import { invoicesService, type InvoiceFilters } from '../api/invoices.api';

export const invoicesQueryKeys = {
  all: ['invoices'] as const,
  list: (filters: Omit<InvoiceFilters, 'cursor'>) =>
    [...invoicesQueryKeys.all, 'list', filters] as const,
  detail: (id: string) => [...invoicesQueryKeys.all, 'detail', id] as const,
  payments: (invoiceId: string) => [...invoicesQueryKeys.all, 'payments', invoiceId] as const,
};

export function useInvoices(filters: Omit<InvoiceFilters, 'cursor'> = {}) {
  return useInfiniteQuery({
    queryKey: invoicesQueryKeys.list(filters),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) =>
      invoicesService.listInvoices({
        ...filters,
        cursor: pageParam,
      }),
    getNextPageParam: (lastPage) =>
      lastPage.meta.has_more ? (lastPage.meta.next_cursor ?? undefined) : undefined,
    staleTime: STALE_INVOICES,
  });
}

export function useInvoiceDetail(id: string) {
  return useQuery({
    queryKey: invoicesQueryKeys.detail(id),
    queryFn: async () => (await invoicesService.getInvoiceDetail(id)).data,
    enabled: Boolean(id),
    staleTime: STALE_INVOICES,
  });
}

export function useInvoicePayments(invoiceId: string) {
  return useQuery({
    queryKey: invoicesQueryKeys.payments(invoiceId),
    queryFn: async () => (await invoicesService.getInvoicePayments(invoiceId)).data,
    enabled: Boolean(invoiceId),
    staleTime: STALE_INVOICES,
  });
}

export function useCreatePayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      invoiceId,
      amount,
      method,
    }: {
      invoiceId: string;
      amount: number;
      method: string;
    }) => invoicesService.createPayment(invoiceId, amount, method),
    onSuccess: async (_data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: invoicesQueryKeys.detail(variables.invoiceId) }),
        queryClient.invalidateQueries({
          queryKey: invoicesQueryKeys.payments(variables.invoiceId),
        }),
        queryClient.invalidateQueries({ queryKey: invoicesQueryKeys.all }),
      ]);
    },
  });
}

export function useUploadProof() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ paymentId, file }: { paymentId: string; file: File }) =>
      invoicesService.uploadPaymentProof(paymentId, file),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: invoicesQueryKeys.all });
    },
  });
}
