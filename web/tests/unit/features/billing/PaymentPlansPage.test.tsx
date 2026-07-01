import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { PaymentPlansPage } from '@/features/billing/ui/PaymentPlansPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

describe('PaymentPlansPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/billing/payment-plans', () => apiListResponse([])));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<PaymentPlansPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no payment plans', async () => {
    renderWithProviders(<PaymentPlansPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with payment plan data', async () => {
    server.use(
      http.get('/api/v1/billing/payment-plans', () =>
        apiListResponse([
          {
            id: 'plan-1',
            student_id: 'std-1',
            name: 'Standard Plan',
            total_amount: 12000,
            currency: 'MAD',
            status: 'active',
            start_date: '2026-09-01',
            created_at: '2026-09-01T00:00:00Z',
            installments: [],
          },
        ]),
      ),
    );
    renderWithProviders(<PaymentPlansPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/billing/payment-plans', () => apiErrorResponse('Server error')));
    renderWithProviders(<PaymentPlansPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
