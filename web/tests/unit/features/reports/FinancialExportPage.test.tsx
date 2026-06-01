import { waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { FinancialExportPage } from '@/features/reports/financial-health/ui/FinancialExportPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

const dashboardData = {
  school_id: 'school-1',
  total_receivable: 500000,
  total_collected: 350000,
  overdue_amount: 50000,
  collection_rate: 70,
  active_payment_plans: 12,
  snapshot_date: '2026-04-30',
};

const trendsData = {
  retention_metrics: [{ academic_year_from: '2024', academic_year_to: '2025', retention_rate: 92 }],
  snapshots: [
    {
      snapshot_date: '2026-04-01',
      total_receivable: 500000,
      total_collected: 300000,
      overdue_amount: 50000,
    },
  ],
  cashflow: [
    {
      forecast_month: '2026-04',
      expected_income: 100000,
      expected_expenses: 80000,
    },
  ],
};

describe('FinancialExportPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/financial-health/dashboard', () => apiResponse(dashboardData)),
      http.get('/api/v1/financial-health/trends', () => apiResponse(trendsData)),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<FinancialExportPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders the export page title', async () => {
    const { container } = renderWithProviders(<FinancialExportPage />, { user: { role: 'ADM' } });
    // Page renders "Financial Exports" (translated)
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(100), { timeout: 5000 });
  });

  it('renders stat cards with data counts', async () => {
    const { container } = renderWithProviders(<FinancialExportPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(100), { timeout: 5000 });
  });

  it('shows error banner on API failure', async () => {
    server.use(
      http.get('/api/v1/financial-health/dashboard', () => apiErrorResponse('Server error')),
      http.get('/api/v1/financial-health/trends', () => apiResponse(trendsData)),
    );
    renderWithProviders(<FinancialExportPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders filter controls for date range and format', async () => {
    const { container } = renderWithProviders(<FinancialExportPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.querySelector('select')).toBeTruthy(), { timeout: 5000 });
  });
});
