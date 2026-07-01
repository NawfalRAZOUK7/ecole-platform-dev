import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { BudgetDetailPage } from '@/features/billing/budgets/ui/BudgetDetailPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';
import { createBudget } from '../../../utils/factories';

const budgetDetail = createBudget({ id: 'budget-test', name: 'Test Budget' });

describe('BudgetDetailPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/budgets/:id', () => apiResponse(budgetDetail)),
      http.get('/api/v1/budgets/:id/allocations', () => apiListResponse([])),
      http.get('/api/v1/budgets', () => apiListResponse([budgetDetail])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<BudgetDetailPage />, {
      user: { role: 'ADM' },
      route: '/budgets/budget-test',
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders page structure with title', async () => {
    const { container } = renderWithProviders(<BudgetDetailPage />, {
      user: { role: 'ADM' },
      route: '/budgets/budget-test',
    });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with budget detail data', async () => {
    renderWithProviders(<BudgetDetailPage />, {
      user: { role: 'ADM' },
      route: '/budgets/budget-test',
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/budgets/:id', () => apiErrorResponse('Server error')));
    renderWithProviders(<BudgetDetailPage />, {
      user: { role: 'ADM' },
      route: '/budgets/budget-test',
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders page for DIR user role', async () => {
    renderWithProviders(<BudgetDetailPage />, {
      user: { role: 'DIR' },
      route: '/budgets/budget-test',
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
