import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { AuditLogPage } from '@/features/admin/ui/AuditLogPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

const mockAuditEntry = {
  id: 'audit-1',
  action_type: 'user.login',
  outcome: 'success',
  actor_id: 'user-1',
  target_type: 'user',
  target_id: 'user-2',
  error_code: null,
  correlation_id: 'corr-12345678',
  ip_address: '192.168.1.1',
  created_at: '2026-01-15T10:30:00Z',
};

describe('AuditLogPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/admin/audit-logs', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
    );
    renderWithProviders(<AuditLogPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('shows empty state when no audit logs', async () => {
    server.use(http.get('/api/v1/admin/audit-logs', () => apiListResponse([])));
    renderWithProviders(<AuditLogPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(document.querySelector('.empty-state__icon')).toBeTruthy();
    });
  });

  it('renders audit log entries successfully', async () => {
    server.use(http.get('/api/v1/admin/audit-logs', () => apiListResponse([mockAuditEntry])));
    renderWithProviders(<AuditLogPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText('user.login')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.1')).toBeInTheDocument();
  });

  it('shows error state when audit logs fail to load', async () => {
    server.use(
      http.get('/api/v1/admin/audit-logs', () => apiErrorResponse('Failed to load audit logs')),
    );
    renderWithProviders(<AuditLogPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load audit logs/)).toBeInTheDocument();
  });
});
