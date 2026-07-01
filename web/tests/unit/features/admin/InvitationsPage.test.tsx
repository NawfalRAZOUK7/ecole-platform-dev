import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { InvitationsPage } from '@/features/admin/ui/InvitationsPage';
import { renderWithProviders } from '../../../utils/render';

const adminHooks = vi.hoisted(() => ({
  useAdminInvitations: vi.fn(),
  useAdminUserSearch: vi.fn(),
  useCreateInvitation: vi.fn(),
  useRevokeInvitation: vi.fn(),
}));

vi.mock('@/features/admin/model/useAdmin', () => ({
  useAdminInvitations: adminHooks.useAdminInvitations,
  useAdminUserSearch: adminHooks.useAdminUserSearch,
  useCreateInvitation: adminHooks.useCreateInvitation,
  useRevokeInvitation: adminHooks.useRevokeInvitation,
}));

const mockInvitation = {
  id: 'invite-1',
  role_target: 'STD',
  consumed_at: null,
  consumed_by: null,
  expires_at: '2026-12-31T00:00:00Z',
  created_at: '2026-01-01T00:00:00Z',
  issuer_user_id: 'user-1',
  status: 'active',
};

function invitationsResult(items: unknown[], error: Error | null = null) {
  return {
    data: error ? undefined : { pages: [{ data: items, meta: { has_more: false } }] },
    error,
    fetchNextPage: vi.fn(),
    hasNextPage: false,
    isFetchingNextPage: false,
    isLoading: false,
    refetch: vi.fn(),
  };
}

describe('InvitationsPage', () => {
  beforeEach(() => {
    adminHooks.useAdminInvitations.mockReturnValue(invitationsResult([]));
    adminHooks.useAdminUserSearch.mockReturnValue({
      data: [],
      isFetching: false,
    });
    adminHooks.useCreateInvitation.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
    adminHooks.useRevokeInvitation.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
  });

  it('renders loading state initially', () => {
    adminHooks.useAdminInvitations.mockReturnValue({
      ...invitationsResult([]),
      isLoading: true,
    });

    renderWithProviders(<InvitationsPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('shows empty state when no invitations', async () => {
    adminHooks.useAdminInvitations.mockReturnValue(invitationsResult([]));

    renderWithProviders(<InvitationsPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        screen.queryByText(/empty/i) ||
          document.querySelector('.empty-state') ||
          document.querySelector('[class*="empty"]'),
      ).toBeTruthy();
    });
  });

  it('renders invitation list successfully', async () => {
    adminHooks.useAdminInvitations.mockReturnValue(invitationsResult([mockInvitation]));

    renderWithProviders(<InvitationsPage />, { user: { role: 'ADM' } });
    // The page renders a table with invitations - look for the revoke button or role badge
    await waitFor(() => {
      expect(document.querySelector('table') || document.querySelector('.role-badge')).toBeTruthy();
    });
  });

  it('shows error state when invitations fail to load', async () => {
    adminHooks.useAdminInvitations.mockReturnValue(
      invitationsResult([], new Error('Failed to load invitations')),
    );

    renderWithProviders(<InvitationsPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load invitations/)).toBeInTheDocument();
  });
});
