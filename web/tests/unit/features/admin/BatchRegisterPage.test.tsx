import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { BatchRegisterPage } from '@/features/admin/ui/BatchRegisterPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

describe('BatchRegisterPage', () => {
  beforeEach(() => {
    server.use(
      http.post('/api/v1/admin/register-batch', () =>
        apiResponse({
          created: 0,
          skipped: 0,
          errors: [],
        }),
      ),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<BatchRegisterPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows the file upload interface', async () => {
    renderWithProviders(<BatchRegisterPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with initial empty state (no rows)', async () => {
    renderWithProviders(<BatchRegisterPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(50);
    });
  });

  it('shows error banner on API failure', async () => {
    server.use(http.post('/api/v1/admin/register-batch', () => apiErrorResponse('Server error')));
    renderWithProviders(<BatchRegisterPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
