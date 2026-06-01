import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { DashboardPage } from '@/features/admin/ui/DashboardPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiResponse, server } from '../../../utils/mocks';

const mockDashboard = {
  users: 150,
  active_sessions: 42,
  active_invitations: 7,
  audit_events_24h: 33,
  pending_justifications: 5,
  users_by_role: { ADM: 2, TCH: 20, STD: 120, PAR: 8 },
};

describe('DashboardPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/admin/dashboard', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiResponse(mockDashboard);
      }),
    );
    renderWithProviders(<DashboardPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders dashboard metrics successfully', async () => {
    server.use(http.get('/api/v1/admin/dashboard', () => apiResponse(mockDashboard)));
    renderWithProviders(<DashboardPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText('150')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('shows users by role breakdown', async () => {
    server.use(http.get('/api/v1/admin/dashboard', () => apiResponse(mockDashboard)));
    renderWithProviders(<DashboardPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(screen.queryByText('120') || screen.queryByText('STD')).toBeTruthy();
    });
  });

  it('shows error state when dashboard fails to load', async () => {
    server.use(
      http.get('/api/v1/admin/dashboard', () => apiErrorResponse('Failed to load dashboard')),
    );
    renderWithProviders(<DashboardPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load dashboard/)).toBeInTheDocument();
  });
});
