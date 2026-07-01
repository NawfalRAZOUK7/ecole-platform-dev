import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { delay, http } from 'msw';
import { describe, expect, it } from 'vitest';
import { BudgetListPage } from '@/features/billing/budgets/ui/BudgetListPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

const budgets = [
  {
    id: 'budget-1',
    name: 'Operations',
    total_amount: 120000,
    spent_amount: 40000,
    remaining_amount: 80000,
    status: 'active' as const,
    currency: 'MAD' as const,
    start_date: '2026-01-01',
    end_date: '2026-12-31',
    created_at: '2026-01-05T08:00:00Z',
  },
  {
    id: 'budget-2',
    name: 'Facilities',
    total_amount: 75000,
    spent_amount: 12000,
    remaining_amount: 63000,
    status: 'frozen' as const,
    currency: 'MAD' as const,
    start_date: '2026-01-01',
    end_date: '2026-12-31',
    created_at: '2026-02-15T08:00:00Z',
  },
];

describe('BudgetListPage', () => {
  it('loads budgets and filters them by status', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('/api/v1/budgets', ({ request }) => {
        const status = new URL(request.url).searchParams.get('status');
        const items = status ? budgets.filter((budget) => budget.status === status) : budgets;
        return apiListResponse(items);
      }),
    );

    renderWithProviders(<BudgetListPage />, {
      user: { role: 'ADM' },
    });

    expect(await screen.findByText('Operations')).toBeInTheDocument();
    expect(screen.getByText('Facilities')).toBeInTheDocument();

    await user.selectOptions(screen.getAllByRole('combobox')[0], 'frozen');

    await waitFor(() => {
      expect(screen.queryByText('Operations')).not.toBeInTheDocument();
    });
    expect(screen.getByText('Facilities')).toBeInTheDocument();
  });

  it('shows an error banner when budgets fail to load', async () => {
    server.use(http.get('/api/v1/budgets', () => apiErrorResponse('Unable to load budgets')));

    renderWithProviders(<BudgetListPage />, {
      user: { role: 'ADM' },
    });

    expect(await screen.findByText('Unable to load budgets')).toBeInTheDocument();
  });

  it('shows loading skeletons while budgets are loading', async () => {
    server.use(
      http.get('/api/v1/budgets', async () => {
        await delay(200);
        return apiListResponse(budgets);
      }),
    );

    const { container } = renderWithProviders(<BudgetListPage />, {
      user: { role: 'ADM' },
    });

    await waitFor(() => {
      expect(container.querySelectorAll('.skeleton--table-row').length).toBeGreaterThan(0);
    });
  });
});
