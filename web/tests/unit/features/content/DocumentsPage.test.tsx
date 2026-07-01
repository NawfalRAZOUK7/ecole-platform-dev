import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { DocumentsPage } from '@/features/content/documents/ui/DocumentsPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, apiResponse, server } from '../../../utils/mocks';

const mockDocument = {
  id: 'doc-1',
  original_filename: 'report-card.pdf',
  filename: 'report-card.pdf',
  mime_type: 'application/pdf',
  size_bytes: 1024000,
  category: 'report',
  linked_student_id: null,
  linked_student_name: null,
  uploader_id: 'user-1',
  uploader_name: 'Mr. Teacher',
  expires_at: null,
  is_expired: false,
  is_expiring_soon: false,
  download_count: 0,
  thumbnail_url: null,
  preview_url: null,
  download_url: null,
  created_at: '2026-01-15T10:00:00Z',
  deduplicated: false,
  can_delete: true,
  can_hard_delete: false,
};

const mockOptions = {
  students: [],
  categories: ['report', 'homework', 'certificate'],
};

function setupHandlers() {
  server.use(
    http.get('/api/v1/documents/options', () => apiResponse(mockOptions)),
    http.get('/api/v1/documents', () => apiListResponse([mockDocument])),
    http.get('/api/v1/resources', () => apiListResponse([])),
  );
}

describe('DocumentsPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/documents/options', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiResponse(mockOptions);
      }),
      http.get('/api/v1/documents', () => apiListResponse([])),
      http.get('/api/v1/resources', () => apiListResponse([])),
    );
    renderWithProviders(<DocumentsPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders document list successfully', async () => {
    setupHandlers();
    renderWithProviders(<DocumentsPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText('report-card.pdf')).toBeInTheDocument();
  });

  it('shows error state when documents fail to load', async () => {
    server.use(
      http.get('/api/v1/documents/options', () => apiResponse(mockOptions)),
      http.get('/api/v1/documents', () => apiErrorResponse('Failed to load documents')),
      http.get('/api/v1/resources', () => apiListResponse([])),
    );
    renderWithProviders(<DocumentsPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        screen.queryByText(/Failed to load documents/) || document.querySelector('[role="alert"]'),
      ).toBeTruthy();
    });
  });
});
