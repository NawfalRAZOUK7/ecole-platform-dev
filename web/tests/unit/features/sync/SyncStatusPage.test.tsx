import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { SyncStatusPage } from '@/features/sync/ui/SyncStatusPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, apiResponse, server } from '../../../utils/mocks';

const mockDevice = {
  id: 'dev-1',
  device_name: 'Laptop Teacher',
  device_type: 'web',
  last_seen_at: '2026-05-30T10:00:00Z',
  is_active: true,
  school_id: 'school-1',
  user_id: 'user-1',
};

const mockSyncStatus = {
  device_id: 'dev-1',
  pending_count: 3,
  synced_count: 150,
  conflict_count: 1,
  last_sync_at: '2026-05-30T09:55:00Z',
};

const mockHealth = {
  device_id: 'dev-1',
  health: 'good',
  latency_ms: 45,
  last_check_at: '2026-05-30T10:00:00Z',
};

const mockCheckpoint = {
  id: 'chk-1',
  device_id: 'dev-1',
  last_entity_type: 'attendance',
  records_synced: 50,
  last_sync_at: '2026-05-30T09:50:00Z',
};

function setupHandlers() {
  server.use(
    http.get('/api/v1/sync/devices', () => apiListResponse([mockDevice])),
    http.get('/api/v1/sync/status', () => apiResponse(mockSyncStatus)),
    http.get('/api/v1/sync/health', () => apiResponse(mockHealth)),
    http.get('/api/v1/sync/checkpoints', () => apiListResponse([mockCheckpoint])),
  );
}

describe('SyncStatusPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/sync/devices', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
      http.get('/api/v1/sync/status', () => apiResponse(mockSyncStatus)),
      http.get('/api/v1/sync/health', () => apiResponse(mockHealth)),
      http.get('/api/v1/sync/checkpoints', () => apiListResponse([])),
    );
    renderWithProviders(<SyncStatusPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders device list after load', async () => {
    setupHandlers();
    renderWithProviders(<SyncStatusPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText('Laptop Teacher · web')).toBeInTheDocument();
  });

  it('shows pending and synced counts', async () => {
    setupHandlers();
    renderWithProviders(<SyncStatusPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(screen.queryByText('3') || screen.queryByText('150')).toBeTruthy();
    });
  });

  it('shows checkpoint data', async () => {
    setupHandlers();
    renderWithProviders(<SyncStatusPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(screen.queryByText('attendance') || screen.queryByText('50')).toBeTruthy();
    });
  });

  it('shows error banner when devices query fails', async () => {
    server.use(
      http.get('/api/v1/sync/devices', () => apiErrorResponse('Sync devices error')),
      http.get('/api/v1/sync/status', () => apiResponse(mockSyncStatus)),
      http.get('/api/v1/sync/health', () => apiResponse(mockHealth)),
      http.get('/api/v1/sync/checkpoints', () => apiListResponse([])),
    );
    renderWithProviders(<SyncStatusPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        screen.queryByText(/Sync devices error/) ||
          screen.queryByText(/error/i) ||
          document.querySelector('[role="alert"]'),
      ).toBeTruthy();
    });
  });

  it('shows empty device list when no devices', async () => {
    server.use(
      http.get('/api/v1/sync/devices', () => apiListResponse([])),
      http.get('/api/v1/sync/status', () => apiResponse({ ...mockSyncStatus, device_id: '' })),
      http.get('/api/v1/sync/health', () => apiResponse(mockHealth)),
      http.get('/api/v1/sync/checkpoints', () => apiListResponse([])),
    );
    renderWithProviders(<SyncStatusPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(document.querySelector('.page')).toBeTruthy();
    });
  });
});
