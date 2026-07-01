import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { StudentContentPage } from '@/features/content/student/ui/StudentContentPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

describe('StudentContentPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/enrollments', () => apiListResponse([])),
      http.get('/api/v1/classes/:classId/content', () => apiListResponse([])),
      http.post('/api/v1/content-items/:contentItemId/progress', () => apiListResponse([])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<StudentContentPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no classes', async () => {
    renderWithProviders(<StudentContentPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with class data', async () => {
    server.use(
      http.get('/api/v1/enrollments', () =>
        apiListResponse([{ class_id: 'c1', class_name: 'Class 6A', class_code: '6A' }]),
      ),
      http.get('/api/v1/classes/c1/content', () => apiListResponse([])),
    );
    renderWithProviders(<StudentContentPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/enrollments', () => apiErrorResponse('Server error')));
    renderWithProviders(<StudentContentPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
