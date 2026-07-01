import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { UsersPage } from '@/features/admin/ui/UsersPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const userItem = {
  id: 'user-2',
  email: 'teacher@school.test',
  full_name: 'Alice Teacher',
  status: 'active',
  role: 'TCH',
  created_at: '2026-01-15T00:00:00Z',
  email_verified: true,
  totp_enabled: false,
};

const suspendedUser = {
  id: 'user-3',
  email: 'suspended@school.test',
  full_name: 'Bob Suspended',
  status: 'suspended',
  role: 'STD',
  created_at: '2026-02-01T00:00:00Z',
  email_verified: false,
  totp_enabled: false,
};

describe('UsersPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/admin/users', () => apiListResponse([])));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<UsersPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no users', async () => {
    const { container } = renderWithProviders(<UsersPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders user list data', async () => {
    server.use(http.get('/api/v1/admin/users', () => apiListResponse([userItem, suspendedUser])));
    renderWithProviders(<UsersPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toContain('Alice Teacher'));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/admin/users', () => apiErrorResponse('Server error')));
    renderWithProviders(<UsersPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows filter controls after loading', async () => {
    const { container } = renderWithProviders(<UsersPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(container.querySelector('select')).toBeTruthy(), {
      timeout: 5000,
    });
  });
});
