import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { STALE_INVOICES } from '@/shared/hooks/useQueryDefaults';
import { invoicesService, type InvoiceFilters } from './invoices.service';

export const invoicesQueryKeys = {
  all: ['invoices'] as const,
  list: (filters: Omit<InvoiceFilters, 'cursor'>) => [...invoicesQueryKeys.all, 'list', filters] as const,
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
      lastPage.meta.has_more ? lastPage.meta.next_cursor ?? undefined : undefined,
    staleTime: STALE_INVOICES,
  });
}

export function useInitiateInvoicePayment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (invoiceId: string) => {
      await invoicesService.initiatePayment(invoiceId);
      return invoiceId;
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: invoicesQueryKeys.all });
    },
  });
}
