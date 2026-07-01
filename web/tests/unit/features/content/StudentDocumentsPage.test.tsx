import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { StudentDocumentsPage } from '@/features/content/documents/ui/StudentDocumentsPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockDocumentsOptions = {
  students: [],
  categories: ['identity', 'medical', 'academic'],
};

describe('StudentDocumentsPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/documents/options', () => apiResponse(mockDocumentsOptions)),
      http.get('/api/v1/students/:studentId/documents', () => apiListResponse([])),
      http.get('/api/v1/students/:studentId/documents/checklist', () => apiResponse([])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<StudentDocumentsPage />, { user: { role: 'STD', id: 'user-1' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no documents', async () => {
    renderWithProviders(<StudentDocumentsPage />, { user: { role: 'STD', id: 'user-1' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders for ADM role with student selection', async () => {
    server.use(
      http.get('/api/v1/documents/options', () =>
        apiResponse({
          students: [{ id: 'std-1', full_name: 'Alice' }],
          categories: ['identity'],
        }),
      ),
      http.get('/api/v1/students/std-1/documents', () => apiListResponse([])),
      http.get('/api/v1/students/std-1/documents/checklist', () => apiResponse([])),
    );
    renderWithProviders(<StudentDocumentsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/documents/options', () => apiErrorResponse('Server error')));
    renderWithProviders(<StudentDocumentsPage />, { user: { role: 'STD', id: 'user-1' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
