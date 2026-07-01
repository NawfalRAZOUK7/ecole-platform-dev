import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { DashboardPage } from '@/features/admin/ui/DashboardPage';
import { renderWithProviders } from '../../../utils/render';

const adminHooks = vi.hoisted(() => ({
  useAdminDashboard: vi.fn(),
}));

vi.mock('@/features/admin/model/useAdmin', () => ({
  useAdminDashboard: adminHooks.useAdminDashboard,
}));

const mockDashboard = {
  users: 150,
  active_sessions: 42,
  active_invitations: 7,
  audit_events_24h: 33,
  pending_justifications: 5,
  users_by_role: { ADM: 2, TCH: 20, STD: 120, PAR: 8 },
};

describe('DashboardPage', () => {
  beforeEach(() => {
    adminHooks.useAdminDashboard.mockReset();
  });

  it('renders loading state initially', () => {
    adminHooks.useAdminDashboard.mockReturnValue({
      data: undefined,
      error: null,
      isLoading: true,
      refetch: vi.fn(),
    });

    renderWithProviders(<DashboardPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders dashboard metrics successfully', async () => {
    adminHooks.useAdminDashboard.mockReturnValue({
      data: mockDashboard,
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });

    renderWithProviders(<DashboardPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText('150')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('shows users by role breakdown', async () => {
    adminHooks.useAdminDashboard.mockReturnValue({
      data: mockDashboard,
      error: null,
      isLoading: false,
      refetch: vi.fn(),
    });

    renderWithProviders(<DashboardPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(screen.queryByText('120') || screen.queryByText('STD')).toBeTruthy();
    });
  });

  it('shows error state when dashboard fails to load', async () => {
    adminHooks.useAdminDashboard.mockReturnValue({
      data: undefined,
      error: new Error('Failed to load dashboard'),
      isLoading: false,
      refetch: vi.fn(),
    });

    renderWithProviders(<DashboardPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load dashboard/)).toBeInTheDocument();
  });
});
