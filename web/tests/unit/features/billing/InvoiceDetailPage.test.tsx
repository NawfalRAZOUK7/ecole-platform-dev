import { Routes, Route } from 'react-router-dom';
import { screen } from '@testing-library/react';
import { delay, http } from 'msw';
import { describe, expect, it } from 'vitest';
import { InvoiceDetailPage } from '@/features/billing/invoices/ui/InvoiceDetailPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiResponse, server } from '../../../utils/mocks';

const invoiceDetail = {
  id: 'invoice-1',
  invoice_number: 'INV-2026-001',
  student_id: 'student-1',
  student_name: 'Amine Student',
  label: 'Tuition - April',
  total_amount: 2400,
  currency: 'MAD',
  status: 'sent',
  issued_date: '2026-04-01',
  due_date: '2026-04-15',
  balance_due: 1200,
  items: [
    {
      id: 'line-1',
      description: 'Tuition April',
      quantity: 1,
      unit_price: 2000,
      amount: 2000,
    },
    {
      id: 'line-2',
      description: 'Transport',
      quantity: 1,
      unit_price: 400,
      amount: 400,
    },
  ],
};

const paymentHistory = [
  {
    id: 'payment-1',
    invoice_id: 'invoice-1',
    amount: 1200,
    method: 'card',
    status: 'paid',
    created_at: '2026-04-02T10:00:00Z',
    finalized_at: '2026-04-02T10:05:00Z',
  },
];

function renderInvoiceDetailPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/invoices/:id" element={<InvoiceDetailPage />} />
    </Routes>,
    {
      route: '/invoices/invoice-1',
      user: { role: 'PAR' },
    },
  );
}

describe('InvoiceDetailPage', () => {
  it('loads invoice detail, displays line items, and shows payment history', async () => {
    server.use(
      http.get('/api/v1/invoices/:id', () => apiResponse(invoiceDetail)),
      http.get('/api/v1/payments/:invoiceId', () => apiResponse(paymentHistory)),
    );

    renderInvoiceDetailPage();

    expect(await screen.findByText('Tuition April')).toBeInTheDocument();
    expect(screen.getByText('Transport')).toBeInTheDocument();
    expect(screen.getByText('Payment history')).toBeInTheDocument();
    expect(screen.getByText('card')).toBeInTheDocument();
  });

  it('shows an error banner when invoice detail fails to load', async () => {
    server.use(
      http.get('/api/v1/invoices/:id', () => apiErrorResponse('Unable to load invoice')),
      http.get('/api/v1/payments/:invoiceId', () => apiResponse(paymentHistory)),
    );

    renderInvoiceDetailPage();

    expect(await screen.findByText('Unable to load invoice')).toBeInTheDocument();
  });

  it('shows a loading state while invoice detail is loading', async () => {
    server.use(
      http.get('/api/v1/invoices/:id', async () => {
        await delay(200);
        return apiResponse(invoiceDetail);
      }),
      http.get('/api/v1/payments/:invoiceId', async () => {
        await delay(200);
        return apiResponse(paymentHistory);
      }),
    );

    renderInvoiceDetailPage();

    expect(screen.getByRole('status', { name: 'Loading...' })).toBeInTheDocument();
  });
});
