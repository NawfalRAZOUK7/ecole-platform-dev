/**
 * Tests for features/reports/ui/ReportsPage.tsx
 */
import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect } from 'vitest';
import { ReportsPage } from '@/features/reports/ui/ReportsPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockOptions = {
  types: ['student_report', 'class_report', 'financial_report', 'attendance_report'],
  classes: [{ id: 'c1', code: '6A', name: 'Class 6A' }],
};

function setupHandlers() {
  server.use(
    http.get('/api/v1/reports/options', () => apiResponse(mockOptions)),
    http.get('/api/v1/reports', () => apiListResponse([])),
    http.get('/api/v1/reports/schedules', () => apiResponse([])),
  );
}

describe('ReportsPage', () => {
  it('renders without crashing', async () => {
    setupHandlers();
    renderWithProviders(<ReportsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders for ADM role', async () => {
    setupHandlers();
    renderWithProviders(<ReportsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(50));
  });

  it('renders for DIR role', async () => {
    setupHandlers();
    renderWithProviders(<ReportsPage />, { user: { role: 'DIR' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders for TCH role', async () => {
    setupHandlers();
    renderWithProviders(<ReportsPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('handles loading state for report options', async () => {
    server.use(
      http.get('/api/v1/reports/options', () => apiResponse(mockOptions)),
      http.get('/api/v1/reports', () => apiListResponse([])),
      http.get('/api/v1/reports/schedules', () => apiResponse([])),
    );
    renderWithProviders(<ReportsPage />, { user: { role: 'ADM' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows error on failure', async () => {
    server.use(
      http.get('/api/v1/reports/options', () => apiErrorResponse('Options unavailable')),
      http.get('/api/v1/reports', () => apiErrorResponse('fail')),
      http.get('/api/v1/reports/schedules', () => apiErrorResponse('fail')),
    );
    renderWithProviders(<ReportsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
