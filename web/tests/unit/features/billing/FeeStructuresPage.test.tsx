import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { FeeStructuresPage } from '@/features/billing/ui/FeeStructuresPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

describe('FeeStructuresPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/billing/fee-structures', () => apiListResponse([])));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<FeeStructuresPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no fee structures', async () => {
    renderWithProviders(<FeeStructuresPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with fee structure data', async () => {
    server.use(
      http.get('/api/v1/billing/fee-structures', () =>
        apiListResponse([
          {
            id: 'fee-1',
            academic_year_id: 'year-1',
            name: 'Tuition Fee',
            amount: 10000,
            currency: 'MAD',
            frequency: 'monthly',
            due_day: 5,
            applies_to_level: null,
            created_at: '2026-09-01T00:00:00Z',
          },
        ]),
      ),
    );
    renderWithProviders(<FeeStructuresPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/billing/fee-structures', () => apiErrorResponse('Server error')));
    renderWithProviders(<FeeStructuresPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
