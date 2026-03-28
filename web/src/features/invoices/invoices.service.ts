import { api } from '@/services/api/client';

export interface Invoice {
  id: string;
  school_id: string;
  student_id: string;
  year_id: string;
  label: string;
  total_cents: number;
  currency: string;
  status: string;
  issued_date: string;
  due_date: string;
  paid_at: string | null;
}

export interface InvoiceFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  status?: string;
}

export const invoicesService = {
  listInvoices(params: InvoiceFilters) {
    return api.list<Invoice>('/invoices', params);
  },

  initiatePayment(invoiceId: string) {
    return api.post<void>('/payments/initiate', {
      invoice_id: invoiceId,
      idempotency_key: `retry-${invoiceId}-${Date.now()}`,
    });
  },
};
