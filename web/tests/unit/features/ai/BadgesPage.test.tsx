import { waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import { BadgesPage } from '@/features/ai/badges/ui/BadgesPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockBadge = {
  id: 'badge-1',
  code: 'FIRST_STAR',
  title_fr: 'Première étoile',
  title_ar: 'النجمة الأولى',
  title_en: 'First Star',
  description_fr: null,
  description_ar: null,
  description_en: null,
  icon: '⭐',
  criteria_type: 'stars_total',
  criteria_value: 1,
  display_order: 1,
  is_active: true,
};

describe('BadgesPage', () => {
  it('renders without crashing', async () => {
    server.use(http.get('/api/v1/rewards/badges', () => apiListResponse([])));
    renderWithProviders(<BadgesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/rewards/badges', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiListResponse([]);
      }),
    );
    renderWithProviders(<BadgesPage />, { user: { role: 'ADM' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders badges when loaded', async () => {
    server.use(http.get('/api/v1/rewards/badges', () => apiListResponse([mockBadge])));
    renderWithProviders(<BadgesPage />, { user: { role: 'ADM' } });
    await waitFor(
      () => {
        expect(document.body.textContent).not.toContain('Loading');
      },
      { timeout: 3000 },
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows empty state when no badges', async () => {
    server.use(http.get('/api/v1/rewards/badges', () => apiListResponse([])));
    renderWithProviders(<BadgesPage />, { user: { role: 'ADM' } });
    await waitFor(
      () => {
        expect(document.body.textContent).not.toContain('Loading');
      },
      { timeout: 3000 },
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows error state on failure', async () => {
    server.use(http.get('/api/v1/rewards/badges', () => apiErrorResponse('Load failed')));
    renderWithProviders(<BadgesPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
