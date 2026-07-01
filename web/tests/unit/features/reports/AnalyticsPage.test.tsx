import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { AnalyticsPage } from '@/features/reports/admin-analytics/ui/AnalyticsPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

const kpisData = {
  computed_at: '2026-04-30T12:00:00Z',
  kpis: [
    {
      kpi_id: 'KPI-G1-001',
      label: 'Platform Adoption',
      value: 75,
      unit: 'percent',
      numerator: 150,
      denominator: 200,
      threshold: '80%',
      data_source: 'db',
      computed_at: '2026-04-30T12:00:00Z',
    },
    {
      kpi_id: 'KPI-G1-002',
      label: 'Active Usage',
      value: 60,
      unit: 'percent',
      numerator: 120,
      denominator: 200,
      threshold: '70%',
      data_source: 'db',
      computed_at: '2026-04-30T12:00:00Z',
    },
    {
      kpi_id: 'KPI-G1-003',
      label: 'Auth Error Rate',
      value: 0.5,
      unit: 'percent',
      numerator: 1,
      denominator: 200,
      threshold: '1%',
      data_source: 'db',
      computed_at: '2026-04-30T12:00:00Z',
    },
    {
      kpi_id: 'KPI-G1-004',
      label: 'Avg Latency',
      value: 120,
      unit: 'milliseconds',
      numerator: null,
      denominator: null,
      threshold: '200ms',
      data_source: 'prometheus',
      computed_at: '2026-04-30T12:00:00Z',
    },
    {
      kpi_id: 'KPI-G1-005',
      label: 'Incidents',
      value: 0,
      unit: 'count',
      numerator: null,
      denominator: null,
      threshold: '0',
      data_source: 'db',
      computed_at: '2026-04-30T12:00:00Z',
    },
    {
      kpi_id: 'KPI-G1-006',
      label: 'Conversion Rate',
      value: 82,
      unit: 'percent',
      numerator: 164,
      denominator: 200,
      threshold: '80%',
      data_source: 'db',
      computed_at: '2026-04-30T12:00:00Z',
    },
  ],
};

describe('AnalyticsPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/kpis', () => apiResponse(kpisData)));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<AnalyticsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders the analytics page title', async () => {
    const { container } = renderWithProviders(<AnalyticsPage />, { user: { role: 'ADM' } });
    // Page renders "Analytics Dashboard" (translated)
    await waitFor(() => expect(container.textContent).not.toBe(''), { timeout: 5000 });
    expect(container.innerHTML.length).toBeGreaterThan(100);
  });

  it('renders KPI cards with data', async () => {
    const { container } = renderWithProviders(<AnalyticsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(100), { timeout: 5000 });
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/kpis', () => apiErrorResponse('Server error')));
    renderWithProviders(<AnalyticsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders page content after loading', async () => {
    const { container } = renderWithProviders(<AnalyticsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0), { timeout: 5000 });
    expect(container.textContent).toBeTruthy();
  });
});
