import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { delay, http } from 'msw';
import { describe, expect, it } from 'vitest';
import { FinancialDashboardPage } from '@/features/reports/financial-health/ui/FinancialDashboardPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiResponse, server } from '../../../utils/mocks';

const dashboard = {
  school_id: 'school-1',
  retention: {
    id: 'retention-1',
    school_id: 'school-1',
    academic_year_from: '2024-2025',
    academic_year_to: '2025-2026',
    total_students_start: 120,
    total_students_end: 118,
    retained: 109,
    new_enrollments: 14,
    withdrawals: 11,
    retention_rate: 91.2,
    computed_at: '2026-04-01T00:00:00Z',
    created_at: '2026-04-01T00:00:00Z',
  },
  snapshot: {
    id: 'snapshot-1',
    school_id: 'school-1',
    snapshot_date: '2026-04-01',
    total_receivable: 580000,
    total_collected: 525000,
    collection_rate: 90.5,
    overdue_amount: 55000,
    overdue_count: 14,
    avg_payment_delay_days: 7,
    currency: 'MAD',
    computed_at: '2026-04-01T00:00:00Z',
    created_at: '2026-04-01T00:00:00Z',
  },
  cashflow: {
    id: 'cashflow-1',
    school_id: 'school-1',
    forecast_month: '2026-04',
    expected_income: 720000,
    expected_expenses: 480000,
    actual_income: 700000,
    actual_expenses: 470000,
    currency: 'MAD',
    confidence_score: 0.82,
    computed_at: '2026-04-01T00:00:00Z',
    created_at: '2026-04-01T00:00:00Z',
  },
};

const trends = {
  school_id: 'school-1',
  retention_metrics: [
    {
      id: 'retention-1',
      school_id: 'school-1',
      academic_year_from: '2024-2025',
      academic_year_to: '2025-2026',
      total_students_start: 120,
      total_students_end: 118,
      retained: 109,
      new_enrollments: 14,
      withdrawals: 11,
      retention_rate: 91.2,
      computed_at: '2026-04-01T00:00:00Z',
      created_at: '2026-04-01T00:00:00Z',
    },
  ],
  snapshots: [dashboard.snapshot],
  cashflow: [dashboard.cashflow],
};

const costPerStudent = {
  id: 'cost-1',
  school_id: 'school-1',
  academic_year_id: '2025-2026',
  total_operational_cost: 390000,
  total_students: 120,
  cost_per_student: 3250,
  revenue_per_student: 4100,
  margin_per_student: 850,
  currency: 'MAD',
  computed_at: '2026-04-01T00:00:00Z',
  created_at: '2026-04-01T00:00:00Z',
};

describe('FinancialDashboardPage', () => {
  it('loads financial data and renders key stat cards', async () => {
    const user = userEvent.setup();

    server.use(
      http.get('/api/v1/financial-health/dashboard', () => apiResponse(dashboard)),
      http.get('/api/v1/financial-health/trends', () => apiResponse(trends)),
      http.get('/api/v1/financial-health/cost-per-student', () => apiResponse(costPerStudent)),
    );

    renderWithProviders(<FinancialDashboardPage />, {
      user: { role: 'ADM' },
    });

    expect(await screen.findByText('91.2%')).toBeInTheDocument();
    expect(
      screen.getByText('Add an academic year ID to load cost-per-student analysis.'),
    ).toBeInTheDocument();

    await user.type(screen.getByRole('textbox'), '2025-2026');

    await waitFor(() => {
      expect(
        screen.queryByText('Add an academic year ID to load cost-per-student analysis.'),
      ).not.toBeInTheDocument();
    });
    expect(screen.getByText('Financial Health')).toBeInTheDocument();
  });

  it('shows an error banner when financial data fails to load', async () => {
    server.use(
      http.get('/api/v1/financial-health/dashboard', () =>
        apiErrorResponse('Unable to load financial dashboard'),
      ),
      http.get('/api/v1/financial-health/trends', () => apiResponse(trends)),
    );

    renderWithProviders(<FinancialDashboardPage />, {
      user: { role: 'ADM' },
    });

    expect(await screen.findByText('Unable to load financial dashboard')).toBeInTheDocument();
  });

  it('shows a loading state while financial data is loading', async () => {
    server.use(
      http.get('/api/v1/financial-health/dashboard', async () => {
        await delay(200);
        return apiResponse(dashboard);
      }),
      http.get('/api/v1/financial-health/trends', async () => {
        await delay(200);
        return apiResponse(trends);
      }),
    );

    renderWithProviders(<FinancialDashboardPage />, {
      user: { role: 'ADM' },
    });

    await waitFor(() => {
      expect(screen.getByRole('status', { name: 'Loading...' })).toBeInTheDocument();
    });
  });
});
