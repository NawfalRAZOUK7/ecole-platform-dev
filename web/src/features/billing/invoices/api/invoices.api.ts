import { api } from '@/core/api/client';

export interface ReportJob {
  id: string;
  type: string;
  status: string;
  download_url: string | null;
  error_message: string | null;
}

export interface InvoiceSummary {
  id: string;
  invoice_number?: string;
  student_id?: string;
  student_name?: string;
  label?: string;
  total_amount?: number;
  total_cents?: number;
  currency?: 'MAD' | string;
  status: string;
  issued_date: string;
  due_date: string;
}

export interface InvoiceLineItem {
  id: string;
  description: string;
  quantity: number;
  unit_price: number;
  amount: number;
}

export interface InvoiceDetail extends InvoiceSummary {
  items: InvoiceLineItem[];
  balance_due?: number;
}

export interface PaymentRecord {
  id: string;
  invoice_id: string;
  amount: number;
  method: string;
  status: string;
  created_at?: string;
  finalized_at?: string | null;
  proof_url?: string | null;
}

export interface InvoiceFilters extends Record<string, string | number | undefined> {
  cursor?: string;
  status?: string;
}

export const invoicesService = {
  listInvoices(params: InvoiceFilters) {
    return api.list<InvoiceSummary>('/invoices', params);
  },

  getInvoiceDetail(id: string) {
    return api.get<InvoiceDetail>(`/invoices/${id}`);
  },

  createPayment(invoiceId: string, amount: number, method: string) {
    return api.post<PaymentRecord>('/payments/initiate', {
      invoice_id: invoiceId,
      amount,
      method,
    });
  },

  uploadPaymentProof(paymentId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<void>(`/payments/${paymentId}/proof`, formData);
  },

  getInvoicePayments(invoiceId: string) {
    return api.get<PaymentRecord[]>(`/payments/${invoiceId}`);
  },

  generateInvoicePdf(invoiceId: string, language: 'fr' | 'ar') {
    return api.post<ReportJob>(`/invoices/${invoiceId}/pdf?language=${language}`);
  },

  generatePaymentReceipt(paymentId: string, language: 'fr' | 'ar') {
    return api.post<ReportJob>(`/payments/${paymentId}/receipt?language=${language}`);
  },

  getReportJobStatus(jobId: string) {
    return api.get<ReportJob>(`/reports/${jobId}/status`);
  },
};
