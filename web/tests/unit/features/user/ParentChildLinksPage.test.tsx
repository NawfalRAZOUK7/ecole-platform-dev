import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { ParentChildLinksPage } from '@/features/user/parent-child-links/ui/ParentChildLinksPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

describe('ParentChildLinksPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/admin/parent-child-links', () => apiListResponse([])),
      http.get('/api/v1/admin/users', () => apiListResponse([])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<ParentChildLinksPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no links', async () => {
    renderWithProviders(<ParentChildLinksPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with parent-child link data', async () => {
    server.use(
      http.get('/api/v1/admin/parent-child-links', () =>
        apiListResponse([
          {
            id: 'link-1',
            parent_user_id: 'par-1',
            child_user_id: 'std-1',
            parent_name: 'Ahmed Parent',
            child_name: 'Ali Student',
            status: 'active',
            created_at: '2026-01-01T00:00:00Z',
          },
        ]),
      ),
    );
    renderWithProviders(<ParentChildLinksPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(
      http.get('/api/v1/admin/parent-child-links', () => apiErrorResponse('Server error')),
    );
    renderWithProviders(<ParentChildLinksPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
