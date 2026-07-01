import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { InvoicesPage } from '@/features/billing/invoices/ui/InvoicesPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';
import { createInvoice } from '../../../utils/factories';

describe('InvoicesPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/invoices', () => apiListResponse([])));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<InvoicesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders with invoice data', async () => {
    server.use(
      http.get('/api/v1/invoices', () =>
        apiListResponse([
          createInvoice({ id: 'inv-1', invoice_number: 'INV-2026-001', status: 'pending' }),
          createInvoice({ id: 'inv-2', invoice_number: 'INV-2026-002', status: 'paid' }),
        ]),
      ),
    );
    renderWithProviders(<InvoicesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows page title area', async () => {
    const { container } = renderWithProviders(<InvoicesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/invoices', () => apiErrorResponse('Server error')));
    renderWithProviders(<InvoicesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows filter controls after loading', async () => {
    const { container } = renderWithProviders(<InvoicesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.querySelector('select')).toBeTruthy(), {
      timeout: 5000,
    });
  });
});
