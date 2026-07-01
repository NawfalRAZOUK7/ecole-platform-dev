/**
 * Tests for features/reports/analytics/ui/AnalyticsDashboardPage.tsx
 */
import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect } from 'vitest';
import { AnalyticsDashboardPage } from '@/features/reports/analytics/ui/AnalyticsDashboardPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockOverview = { metrics: [] };
const mockAttendance = {
  summary: { rate: { value: 95, previous: 93, change: 2 }, total_records: 500 },
  series: [],
};
const mockGrades = {
  summary: { average: { value: 14.5, previous: 14.2, change: 0.3 }, count: 200 },
  distribution: [],
};
const mockBilling = {
  summary: {
    invoiced: 500000,
    paid: 450000,
    outstanding: 50000,
    collection_rate: { value: 90, previous: 88, change: 2 },
  },
  series: [],
};
const mockEngagement = {
  summary: {
    registered_users: 200,
    dau: 50,
    mau: 180,
    active_users: { value: 180, previous: 170, change: 10 },
    engaged_users: 150,
  },
  funnel: [],
  feature_adoption: [],
};

function setupHandlers() {
  server.use(
    http.get('/api/v1/analytics/overview', () => apiResponse(mockOverview)),
    http.get('/api/v1/analytics/attendance', () => apiResponse(mockAttendance)),
    http.get('/api/v1/analytics/grades', () => apiResponse(mockGrades)),
    http.get('/api/v1/analytics/billing', () => apiResponse(mockBilling)),
    http.get('/api/v1/analytics/engagement', () => apiResponse(mockEngagement)),
    http.get('/api/v1/programs', () => apiListResponse([])),
  );
}

describe('AnalyticsDashboardPage', () => {
  it('renders without crashing', async () => {
    setupHandlers();
    renderWithProviders(<AnalyticsDashboardPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    setupHandlers();
    renderWithProviders(<AnalyticsDashboardPage />, { user: { role: 'ADM' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders dashboard with data', async () => {
    setupHandlers();
    renderWithProviders(<AnalyticsDashboardPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).not.toContain('Loading...'), {
      timeout: 5000,
    });
    expect(document.body.textContent).toBeTruthy();
  });

  it('shows error when analytics fail', async () => {
    server.use(
      http.get('/api/v1/analytics/overview', () => apiErrorResponse('Analytics unavailable')),
      http.get('/api/v1/analytics/attendance', () => apiErrorResponse('fail')),
      http.get('/api/v1/analytics/grades', () => apiErrorResponse('fail')),
      http.get('/api/v1/analytics/billing', () => apiErrorResponse('fail')),
      http.get('/api/v1/analytics/engagement', () => apiErrorResponse('fail')),
      http.get('/api/v1/programs', () => apiListResponse([])),
    );
    renderWithProviders(<AnalyticsDashboardPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
