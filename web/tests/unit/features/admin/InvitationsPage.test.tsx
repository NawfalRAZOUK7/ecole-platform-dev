import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { InvitationsPage } from '@/features/admin/ui/InvitationsPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

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

describe('InvitationsPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/admin/invitations', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
    );
    renderWithProviders(<InvitationsPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('shows empty state when no invitations', async () => {
    server.use(http.get('/api/v1/admin/invitations', () => apiListResponse([])));
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
    server.use(http.get('/api/v1/admin/invitations', () => apiListResponse([mockInvitation])));
    renderWithProviders(<InvitationsPage />, { user: { role: 'ADM' } });
    // The page renders a table with invitations - look for the revoke button or role badge
    await waitFor(() => {
      expect(document.querySelector('table') || document.querySelector('.role-badge')).toBeTruthy();
    });
  });

  it('shows error state when invitations fail to load', async () => {
    server.use(
      http.get('/api/v1/admin/invitations', () => apiErrorResponse('Failed to load invitations')),
    );
    renderWithProviders(<InvitationsPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load invitations/)).toBeInTheDocument();
  });
});
